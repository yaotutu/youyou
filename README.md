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

- 📍 物品位置记忆：记录和查询物品存放位置
- 💬 智能对话：自然语言交互
- 🔀 多Agent架构：Supervisor + ItemAgent + ChatAgent
- 💾 语义记忆：基于 mem0 和 Qdrant 的向量存储
- 🔌 RESTful API：标准 OpenAPI/Swagger 接口
- 📚 交互式文档：内置 Swagger UI

## 项目结构

```
youyou/
├── docs/                    # 文档
│   ├── README.md           # 详细文档
│   ├── QUICKSTART.md       # 快速开始指南
│   ├── CLIENT_SERVER_GUIDE.md  # 客户端-服务端指南
│   └── TROUBLESHOOTING.md  # 问题排查
├── src/youyou/
│   ├── agents/             # Agents
│   │   ├── item_agent/    # 物品管理 Agent
│   │   ├── chat_agent/    # 对话 Agent
│   │   └── supervisor/    # 协调 Agent
│   ├── core/              # 核心模块
│   │   └── memory.py      # 记忆管理
│   ├── tools/             # 公共工具
│   ├── config.py          # 配置
│   ├── server.py          # 服务端
│   └── cli.py             # 客户端
├── tests/                  # 测试文件
└── data/                   # 数据存储（自动创建）
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

## 更多文档

- [API 文档](docs/API.md) - 完整的 API 接口文档
- [使用示例](docs/EXAMPLES.md) - 各种语言的使用示例
- [快速开始](docs/QUICKSTART.md) - 详细的快速开始指南
- [问题排查](docs/TROUBLESHOOTING.md) - 常见问题解决方案
