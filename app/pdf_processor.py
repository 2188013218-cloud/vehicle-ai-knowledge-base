"""
PDF 处理器
功能：读取 PDF 文件 → 提取文字 → 切成文本块（Chunk）
"""

from PyPDF2 import PdfReader
from config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    读取 PDF 文件，提取所有文字

    参数：
        pdf_path: PDF 文件路径

    返回：
        合并后的纯文本字符串
    """
    reader = PdfReader(pdf_path)
    all_text = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text.strip():  # 跳过空白页
            all_text.append(text)

    return "\n".join(all_text)


def chunk_text(text: str) -> list[str]:
    """
    将长文本切成小块（Chunk），方便后续向量化

    切块策略：
        - 每块 CHUNK_SIZE 个字符
        - 相邻块之间重叠 CHUNK_OVERLAP 个字符
        - 这样不会把一句话切在中间导致意义丢失

    参数：
        text: 从 PDF 提取的完整文本

    返回：
        字符串列表，每个元素是一个 Chunk
    """
    chunks = []
    start = 0

    while start < len(text):
        # 取从 start 开始、长度 CHUNK_SIZE 的一段
        end = start + CHUNK_SIZE
        chunk = text[start:end]

        if chunk:  # 非空才加入
            chunks.append(chunk)

        # 下一次的起点 = 当前起点 + 步长 - 重叠
        step = CHUNK_SIZE - CHUNK_OVERLAP
        start += step

    return chunks


def process_pdf(pdf_path: str) -> list[str]:
    """
    一键处理：读 PDF → 切块

    这是 pdf_processor 对外的统一接口，
    其他模块只需要调用这一个函数就行。

    参数：
        pdf_path: PDF 文件路径

    返回：
        文本块列表
    """
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    return chunks
