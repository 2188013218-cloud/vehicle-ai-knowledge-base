# 🚗 AI 车辆故障知识库

> 车辆工程 × AI
>• 基于 RAG 构建汽车维修知识库，实现维修文档语义检索。

>• 使用 FastAPI 构建后端接口，FAISS 建立向量索引，支持 PDF 维修手册问答。

>• 采用 OpenAI Compatible API（FreellmAPI）接入大语言模型，实现专业维修知识问答
上传 PDF 维修手册 → AI 自动阅读 → 提问即可获取答案

## 快速开始

### 方式一：自动配置（推荐）

```bash
# 1. 下载项目
git clone https://github.com/2188013218-cloud/vehicle-ai-knowledge-base.git
cd vehicle-ai-knowledge-base

# 2. 运行配置向导
python setup.py

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python main.py

# 5. 打开浏览器访问 http://localhost:8000
```

### 方式二：手动配置

```bash
# 1. 复制配置文件
cp config.example.py config.py
# 然后编辑 config.py，填入你的 API 地址和 Key

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python main.py

# 4. 打开浏览器访问
# http://localhost:8000
```

> **注意**：首次运行会自动下载向量模型（约 80MB），之后离线可用。
> 如果下载失败，科学上网后重试即可。

## 技术栈

| 技术 | 用途 |
|------|------|
| **Python** | 开发语言 |
| **FastAPI** | Web 框架，提供 RESTful API |
| **FAISS** | 向量检索引擎（毫秒级检索） |
| **Sentence-Transformers** | 本地文本向量化模型 |
| **OpenAI / FreellmAPI** | LLM 问答接口 |
| **RAG 架构** | 检索增强生成 |
| **PyPDF2** | PDF 解析与文本提取 |

## 架构

```
用户上传 PDF → PDF 解析 & 切块 → 向量化 → FAISS 索引
                                              ↓
用户提问     → 问题向量化 → FAISS 检索 → 找到相关段落
                                              ↓
                                     LLM 生成回答 ← 参考原文
```

## 功能

- ✅ 上传 PDF 车辆维修手册
- ✅ 自动切块、向量化、建索引
- ✅ 基于手册内容智能问答
- ✅ 智能推荐相关问题（自动识别手册覆盖的领域）
- ✅ 索引持久化（重启后自动加载）
- ✅ 美观的中文 Web 界面

## 适合谁

- 🚗 **车辆工程专业学生** — 展示专业 + AI 的交叉能力
- 🔧 **维修技术人员** — 快速查询维修手册
- 💡 **AI 初学者** — 学习 RAG 架构的完整实现

## 项目亮点

> "用 RAG 架构解决了 LLM 在专业领域知识不足的问题，让 AI 基于实际的维修手册内容回答问题，避免了 AI 幻觉。"

## 使用示例

1. 启动服务后打开 `http://localhost:8000`
2. 点击上传区域，选择一份车辆维修手册 PDF
3. 等待系统自动处理（切块 → 向量化 → 建索引）
4. 在提问框输入问题，或点击快捷提问按钮
5. AI 基于手册内容给出专业回答
