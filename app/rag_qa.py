"""
RAG 问答模块
功能：用户提问 → 检索相关 Chunk → 拼 Prompt → LLM 回答

这就是 RAG（检索增强生成）的最后一步：
  没有让 LLM 凭空回答，而是先给了它参考资料
"""

from openai import OpenAI
from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME

# 初始化 LLM 客户端
client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

# 系统提示词：告诉 LLM 它是什么角色、该怎么回答
SYSTEM_PROMPT = """你是一个专业的车辆故障诊断助手。用户上传了维修手册让你阅读，你需要直接给出答案。

规则：
1. 我会提供一些维修手册片段作为依据
2. 直接从资料中提取答案告诉用户，语气要像"我查了手册，答案是..."
3. 绝对不能出现"请参考PDF"、"详见手册"、"查阅资料"、"请看附件"这类话
4. 如果资料中有相关内容，直接整理出来回答，不要问用户要不要看
5. 如果资料里确实没有相关信息，直接说"手册中没有找到相关内容"
6. 如果是维修步骤，按步骤整理清楚

回答要求：
- 用中文回答，口语化、清晰
- 给出具体原因和解决方法
- 语气专业但亲切，像修车师傅在跟你聊天"""


def ask_question(query: str, context_chunks: list[dict]) -> str:
    """
    用户提问 → 生成答案

    流程：
        1. 把检索到的 Chunk 拼成"参考资料"
        2. 构造 Prompt：系统提示词 + 参考资料 + 用户问题
        3. 发给 LLM
        4. 返回答案

    参数：
        query:          用户的问题（如 "发动机故障灯亮了怎么办"）
        context_chunks: vector_store.search() 返回的结果列表
                        [{"chunk": "...", "score": 0.92}, ...]

    返回：
        LLM 生成的回答文本
    """
    # ===== 1. 拼参考资料 =====
    context_text = ""
    for i, item in enumerate(context_chunks):
        context_text += f"\n【资料片段 {i+1}】\n{item['chunk']}\n"

    # ===== 2. 构造 Prompt =====
    user_prompt = f"""请根据以下车辆维修手册资料，回答用户的问题。

参考资料：
{context_text}

用户问题：{query}

请基于参考资料给出专业、准确的回答。"""

    # ===== 3. 调 LLM =====
    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3  # 低温度 = 更准确的回答
    )

    # ===== 4. 返回答案 =====
    answer = response.choices[0].message.content
    return answer
