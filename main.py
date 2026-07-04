"""
FastAPI 应用入口
功能：启动 Web 服务，提供上传 PDF 和提问的接口

API 接口：
  POST /upload    上传 PDF 维修手册，自动建库
  GET  /ask       提问，返回 AI 回答
  GET  /api/status   服务状态
  GET  /api/suggest-questions  智能推荐问题
  GET  /          前端页面
"""

import os
import uuid
import glob
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.pdf_processor import process_pdf
from app.vector_store import VectorStore
from app.rag_qa import ask_question

# ==================== 初始化 ====================

app = FastAPI(title="AI 车辆故障知识库", version="1.0.0")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

vector_store = VectorStore()
UPLOAD_DIR = "data/uploads"
FAISS_DIR = "data/faiss_index"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

# 启动时自动加载上次的索引（如果有的话）
index_files = glob.glob(os.path.join(FAISS_DIR, "*.faiss"))
if index_files:
    # 取最新的 .faiss 文件
    latest_index = max(index_files, key=os.path.getmtime)
    index_name = os.path.splitext(os.path.basename(latest_index))[0]
    try:
        vector_store.load(index_name)
        print(f"已自动加载索引: {index_name}")
    except Exception as e:
        print(f"加载索引失败: {e}")


# ==================== 接口一：上传 PDF ====================

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    上传 PDF 维修手册

    流程：
        1. 保存上传的 PDF 文件
        2. 解析 PDF → 切块
        3. 建立 FAISS 向量索引
        4. 返回处理结果

    测试方式（在终端执行）：
        curl -X POST http://localhost:8000/upload \\
            -F "file=@你的维修手册.pdf"
    """
    # 1. 检查文件格式
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "只支持 PDF 文件")

    # 2. 保存文件
    file_id = str(uuid.uuid4())[:8]  # 生成唯一 ID
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 3. 解析 PDF → 切块
    print(f"正在处理: {file.filename}")
    chunks = process_pdf(save_path)
    print(f"切成了 {len(chunks)} 个文本块")

    # 4. 建 FAISS 索引
    index_name = file_id
    vector_store.build_index(chunks, index_name)

    return {
        "message": "PDF 处理完成",
        "filename": file.filename,
        "chunks": len(chunks),
        "index_name": index_name
    }


# ==================== 接口二：提问 ====================

@app.get("/ask")
async def ask(query: str):
    """
    提问：检索资料 → LLM 回答

    参数（GET 参数形式）：
        query: 用户的问题

    流程：
        1. 检查是否已有索引
        2. FAISS 检索相关 Chunk
        3. 发给 LLM 生成答案
        4. 返回答案 + 参考资料

    测试方式：
        curl "http://localhost:8000/ask?query=发动机故障灯亮了怎么办"
    """
    if vector_store.index is None:
        raise HTTPException(400, "请先上传 PDF 维修手册")

    # 1. 检索
    results = vector_store.search(query)

    # 2. 生成答案
    answer = ask_question(query, results)

    # 3. 返回结果（包含参考资料，方便调试）
    return {
        "query": query,
        "answer": answer,
        "references": [
            {"chunk": r["chunk"][:100] + "...", "score": r["score"]}
            for r in results
        ]
    }


# ==================== 接口三：健康检查 ====================

@app.get("/")
async def root():
    """返回中文前端页面"""
    return FileResponse("static/index.html")

@app.get("/api/status")
async def api_status():
    """返回服务状态（JSON 格式，供前端调用）"""
    return {
        "service": "AI 车辆故障知识库",
        "status": "running",
        "index_loaded": vector_store.index is not None,
        "chunks_count": len(vector_store.chunks) if vector_store.index else 0
    }

@app.get("/api/suggest-questions")
async def suggest_questions():
    """
    根据已上传的 PDF 内容，推荐相关问题

    原理：对每个预定义的车辆问题关键词，
    用 FAISS 检索手册中是否有相关内容，
    只返回相似度高的（即手册里有答案的）问题
    """
    if vector_store.index is None:
        return {"questions": []}

    # 预定义的问题模板 [关键词, 问题]
    question_templates = [
        ["发动机故障灯", "发动机故障灯亮了怎么办？"],
        ["变速箱", "变速箱异响是什么原因？"],
        ["刹车", "刹车时有异响怎么回事？"],
        ["方向盘", "方向盘跑偏怎么解决？"],
        ["水温过高", "水温过高是什么问题？"],
        ["启动困难", "启动困难怎么排查？"],
        ["空调", "空调不制冷是什么原因？"],
        ["油耗", "油耗突然增加怎么办？"],
        ["发动机异响", "发动机有异响是什么问题？"],
        ["轮胎", "轮胎气压不足怎么办？"],
        ["离合器", "离合器打滑是什么原因？"],
        ["电瓶", "电瓶亏电怎么处理？"],
        ["机油", "机油灯亮了怎么办？"],
        ["ABS", "ABS故障灯亮了是什么原因？"],
        ["安全气囊", "安全气囊灯亮怎么回事？"],
    ]

    related_questions = []
    for keyword, question in question_templates:
        try:
            results = vector_store.search(keyword, k=3)
            # 取前3个结果的平均分，并且至少有一个>0.5才算相关
            if results and len(results) >= 1:
                avg_score = sum(r["score"] for r in results) / len(results)
                if avg_score > 0.45 and results[0]["score"] > 0.5:
                    related_questions.append(question)
        except:
            continue

    return {"questions": related_questions}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    print("🚗 AI 车辆故障知识库启动中...")
    print("接口文档：http://localhost:8000/docs")
    print("上传接口：POST http://localhost:8000/upload")
    print("提问接口：POST http://localhost:8000/ask?query=你的问题")
    uvicorn.run(app, host="0.0.0.0", port=8000)
