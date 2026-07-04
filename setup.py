"""
🚗 AI 车辆故障知识库 - 首次配置向导

自动检测配置并引导你完成设置
"""

import os

# ========== 检测配置文件 ==========
if not os.path.exists("config.py"):
    print("=" * 50)
    print("  🚗 AI 车辆故障知识库 - 首次配置")
    print("=" * 50)
    print()
    print("未检测到 config.py，正在创建...")
    print()

    # 复制示例配置
    if os.path.exists("config.example.py"):
        with open("config.example.py", "r", encoding="utf-8") as f:
            example = f.read()
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(example)
    else:
        # 没有示例文件，直接创建
        with open("config.py", "w", encoding="utf-8") as f:
            f.write('"""\n配置文件\n"""\n\n')
            f.write('LLM_BASE_URL = "http://localhost:3001/v1"\n')
            f.write('LLM_API_KEY = "请替换为你的 API Key"\n')
            f.write('LLM_MODEL_NAME = "auto"\n')
            f.write('FAISS_INDEX_PATH = "data/faiss_index"\n')
            f.write('CHUNK_SIZE = 500\n')
            f.write('CHUNK_OVERLAP = 50\n')
            f.write('TOP_K = 3\n')

    print("✅ config.py 已创建！")
    print()

# ========== 读取配置 ==========
with open("config.py", "r", encoding="utf-8") as f:
    config_content = f.read()

# ========== 检查 API Key ==========
has_valid_key = True
if "LLM_API_KEY" in config_content:
    # 提取 API Key 值
    for line in config_content.split("\n"):
        if line.strip().startswith("LLM_API_KEY"):
            key_value = line.split("=")[1].strip().strip('"').strip("'")
            placeholder_values = ["你的 API Key", "请替换为你的 API Key", "your-api-key", ""]
            if key_value in placeholder_values or len(key_value) < 5:
                has_valid_key = False

if not has_valid_key:
    print()
    print("⚠️  检测到 API Key 尚未配置！")
    print()
    print("你需要一个 LLM API Key 才能使用问答功能。")
    print()
    print("选项 1: 使用 OpenAI")
    print("  1. 访问 https://platform.openai.com/api-keys")
    print("  2. 创建一个 API Key")
    print("  3. 编辑 config.py，填入：")
    print("     LLM_BASE_URL = 'https://api.openai.com/v1'")
    print("     LLM_API_KEY = 'sk-你的key'")
    print()
    print("选项 2: 使用 FreellmAPI（需自行搭建）")
    print("  1. 确保 freellmapi 在本地运行")
    print("  2. 编辑 config.py 填入你的 API Key")
    print()
    print("选项 3: 使用其他 OpenAI 兼容 API")
    print("  修改 config.py 中的 LLM_BASE_URL 和 LLM_API_KEY")
    print()
else:
    print("✅ API Key 已配置")
    print()

# ========== 安装依赖 ==========
print("检查依赖...")
try:
    import fastapi
    import faiss
    import PyPDF2
    print("✅ 核心依赖已安装")
except ImportError as e:
    print(f"⚠️  缺少依赖: {e}")
    print("运行: pip install -r requirements.txt")
    print()

print("=" * 50)
print("  配置完成！运行 python main.py 启动服务")
print("=" * 50)
