"""
配置文件
所有需要调整的参数都集中在这里，方便后续修改
"""

import os

# ==================== LLM API 配置 ====================
# 使用 OpenAI 兼容接口，对接你的 freellmapi
LLM_BASE_URL = "http://localhost:3001/v1"  # freellmapi 本地地址
LLM_API_KEY = "freellmapi-1d4e2b7b1be641ba4bacce393bc981deb201566a5b8a5963"
LLM_MODEL_NAME = "auto"  # auto 自动路由到最佳免费模型

# ==================== FAISS 配置 ====================
FAISS_INDEX_PATH = "data/faiss_index"  # FAISS 索引文件存放目录

# ==================== PDF 处理配置 ====================
CHUNK_SIZE = 500        # 每个文本块的字数
CHUNK_OVERLAP = 50      # 相邻块之间的重叠字数（保持上下文连贯）

# ==================== 检索配置 ====================
TOP_K = 3  # 用户提问时，检索最相似的几个 Chunk 送给 LLM
