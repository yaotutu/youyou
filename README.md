# YouYou - 本地智能助手

YouYou 是一个基于 LangChain 1.0 的本地智能助手系统，具有物品位置记忆和对话功能。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动服务（自动清理端口占用）
uv run youyou-server
```

服务启动后，访问：
- **Swagger UI**: http://127.0.0.1:8000/docs
- **API 基础地址**: http://127.0.0.1:8000/api/v1

**注意**: 如果端口 8000 被占用，服务会自动终止占用端口的进程并继续启动。

## 功能特性

- 📍 **物品位置记忆**：记录和查询物品存放位置
- 💬 **智能对话**：自然语言交互
- 📝 **笔记本系统**：智能笔记管理和知识存储（新增）
  - 💡 保存灵感、想法、文章摘要
  - 🔗 自动分析 GitHub 项目
  - 🔍 混合搜索（关键词 + 语义）
  - 🏷️ 自动标签提取
  - 🎯 **标记路由**：支持 `#note` 标记明确触发
- 🔀 **多Agent架构**：Supervisor + ItemAgent + ChatAgent + NoteAgent
- 💾 **语义记忆**：基于 mem0 和 Qdrant 的向量存储
- 🔌 **RESTful API**：标准 OpenAPI/Swagger 接口
- 📚 **交互式文档**：内置 Swagger UI

## 项目结构

```
youyou/
├── docs/                    # 文档
│   ├── README.md           # 详细文档
│   ├── QUICKSTART.md       # 快速开始指南
│   ├── CLIENT_SERVER_GUIDE.md  # 客户端-服务端指南
│   ├── note_agent_guide.md # NoteAgent 使用指南（新增）
│   └── TROUBLESHOOTING.md  # 问题排查
├── src/youyou/
│   ├── agents/             # Agents
│   │   ├── item_agent/    # 物品管理 Agent
│   │   ├── chat_agent/    # 对话 Agent
│   │   ├── note_agent/    # 笔记本 Agent（新增）
│   │   └── supervisor/    # 协调 Agent
│   ├── core/              # 核心模块
│   │   └── memory.py      # 记忆管理
│   ├── tools/             # 公共工具
│   ├── config.py          # 配置
│   ├── server.py          # 服务端
│   └── cli.py             # 客户端
├── scripts/                # 测试脚本
│   └── test_note_agent.py # NoteAgent 测试（新增）
├── tests/                  # 测试文件
└── data/                   # 数据存储（自动创建）
    ├── qdrant/            # 向量数据库（物品记忆）
    └── notes/             # 笔记数据（新增）
        ├── notes.db       # SQLite 数据库
        └── qdrant/        # Qdrant 向量库
```

## 配置

复制 `.env.example` 到 `.env` 并配置：

```bash
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_API_KEY=your_api_key_here
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
```

## API 使用

### 使用 Swagger UI（推荐）

访问 http://127.0.0.1:8000/docs 使用交互式 API 文档。

### 使用 curl

```bash
# 记录物品位置
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "钥匙放在书桌抽屉里"}'

# 查询物品位置
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "钥匙在哪？"}'
```

### 使用 Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/v1/chat/message",
    json={"message": "钥匙放在书桌抽屉里"}
)
print(response.json()['response'])
```

## 使用示例

### 笔记本功能（新增）

#### 使用标记路由（推荐）

```bash
# 使用 #note 标记保存笔记（直接路由，跳过 Supervisor）
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "#note Python 装饰器可以实现缓存功能"}'

# 使用中文标记
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "#笔记 Rust 的所有权系统很强大"}'

# GitHub 项目自动识别（无需标记）
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "https://github.com/langchain-ai/langchain"}'

# 搜索笔记
curl -X POST http://127.0.0.1:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "我之前收藏的 FastAPI 项目在哪？"}'
```

**标记说明**：
- `#note` 或 `#笔记`：明确保存笔记
- `/note` 或 `/笔记`：备用格式
- GitHub URL：自动识别并分析

查看完整标记列表和使用指南：[NoteAgent 使用指南](docs/note_agent_guide.md#🏷️-标记系统推荐使用)

## 更多文档

- [NoteAgent 使用指南](docs/note_agent_guide.md) - 笔记本功能详细文档（新增）
- [API 文档](docs/API.md) - 完整的 API 接口文档
- [使用示例](docs/EXAMPLES.md) - 各种语言的使用示例
- [快速开始](docs/QUICKSTART.md) - 详细的快速开始指南
- [问题排查](docs/TROUBLESHOOTING.md) - 常见问题解决方案
