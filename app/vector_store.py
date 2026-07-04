"""
向量存储模块
功能：文本块 → 向量 → FAISS 索引 → 持久化 → 检索

整个 RAG 的核心在这里：
  1. 建库：把 Chunk 变成向量存到 FAISS
  2. 检索：用户提问 → 转向量 → FAISS 找最相似的 Chunk
"""

import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, TOP_K

# 加载本地向量模型（支持中文的轻量模型）
# 第一次运行会自动下载（约 80MB），之后直接使用缓存
print("正在加载向量模型（首次会下载约 80MB）...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("向量模型加载完成！")


class VectorStore:
    """
    FAISS 向量存储

    使用示例：
        store = VectorStore()
        store.build_index(["块1", "块2", ...], "manual_v1")
        results = store.search("发动机故障码")
    """

    def __init__(self):
        """初始化：FAISS 索引和 Chunk 原文列表"""
        self.index = None       # FAISS 索引对象
        self.chunks = []        # 对应的 Chunk 原文
        self.index_name = ""    # 索引名称（用于区分不同文档）

    # ==================== 向量化 ====================

    def _get_embedding(self, text: str) -> list[float]:
        """
        用本地模型把一段文字变成向量

        原理：
            文字 "发动机故障" → 模型 → [0.023, -0.015, ..., 0.087]
            这样计算机就能计算文字之间的"相似度"
        """
        return embedder.encode(text).tolist()

    # ==================== 建库 ====================

    def build_index(self, chunks: list[str], index_name: str = "default"):
        """
        把 Chunk 列表建成 FAISS 索引

        流程：
            1. 所有 Chunk 一次性变成向量（本地模型，批量处理）
            2. 所有向量 → 存入 FAISS
            3. 保存到硬盘，下次启动不用重新建

        参数：
            chunks:      文本块列表（从 pdf_processor 来的）
            index_name:  索引名称（一个 PDF 一个名字）
        """
        print(f"正在将 {len(chunks)} 个文本块转为向量（本地模型）...")

        if not chunks:
            print("警告：没有文本块，跳过建库")
            return

        # 批量转向量（比逐个循环快很多）
        vectors_array = embedder.encode(chunks).astype("float32")

        # 获取向量的维度（例如 1536 维）
        dimension = vectors_array.shape[1]

        # 创建 FAISS 索引（IndexFlatIP = 内积索引，用于余弦相似度）
        self.index = faiss.IndexFlatIP(dimension)

        # 把向量加入索引
        self.index.add(vectors_array)

        # 保存 Chunk 原文
        self.chunks = chunks
        self.index_name = index_name

        print(f"建库完成！共 {len(chunks)} 个向量，维度 {dimension}")

        # 保存到硬盘
        self._save()

    # ==================== 检索 ====================

    def search(self, query: str, k: int = TOP_K) -> list[dict]:
        """
        用户提问 → 找最相关的 Chunk

        流程：
            1. 问题 → 转成向量
            2. FAISS 找最相似的 k 个 Chunk（余弦相似度）
            3. 返回 Chunk 原文 + 相似度分数

        参数：
            query: 用户的问题（如 "发动机故障码P0301是什么"）
            k:     返回几个最相关的结果

        返回：
            [
                {"chunk": "原文...", "score": 0.92},
                {"chunk": "原文...", "score": 0.85},
                ...
            ]
        """
        if self.index is None:
            raise ValueError("请先建库（调用 build_index）")

        # 问题 → 向量
        query_vec = self._get_embedding(query)
        query_array = np.array([query_vec]).astype("float32")

        # FAISS 搜索：找最相似的 k 个
        scores, indices = self.index.search(query_array, k)

        # 整理结果
        results = []
        for i in range(k):
            idx = indices[0][i]
            if idx < len(self.chunks):  # 防止越界
                results.append({
                    "chunk": self.chunks[idx],
                    "score": float(scores[0][i])
                })

        return results

    # ==================== 持久化 ====================

    def _save(self):
        """
        把 FAISS 索引 + Chunk 原文保存到硬盘

        这样程序重启后不用重新建库
        """
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

        # 保存 FAISS 索引
        index_path = os.path.join(FAISS_INDEX_PATH, f"{self.index_name}.faiss")
        faiss.write_index(self.index, index_path)

        # 保存 Chunk 原文（用 pickle 序列化）
        chunks_path = os.path.join(FAISS_INDEX_PATH, f"{self.index_name}.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

        print(f"索引已保存到 {FAISS_INDEX_PATH}")

    def load(self, index_name: str):
        """
        从硬盘加载之前建好的索引

        参数：
            index_name: 之前建库时用的名称
        """
        # 加载 FAISS 索引
        index_path = os.path.join(FAISS_INDEX_PATH, f"{index_name}.faiss")
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"找不到索引文件：{index_path}")

        self.index = faiss.read_index(index_path)

        # 加载 Chunk 原文
        chunks_path = os.path.join(FAISS_INDEX_PATH, f"{index_name}.pkl")
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)

        self.index_name = index_name
        print(f"已加载索引 '{index_name}'，共 {len(self.chunks)} 个 Chunk")
