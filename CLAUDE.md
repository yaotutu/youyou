# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

YouYou 是一个基于 LangChain 1.0 的本地智能助手系统，采用多 Agent 架构，支持物品位置记忆和对话功能。

## 目录结构

```
src/
  agents/         # Agent 模块
  core/           # 核心组件
  tools/          # 工具模块
  config.py       # 配置管理
  server.py       # Flask 服务器
  youyou/         # 包入口（兼容 uv）
    __init__.py
scripts/          # 测试和工具脚本
tests/            # 单元测试
```

**重要说明**：
- `src/` 下直接包含主要模块，无需再嵌套 `youyou/` 目录
- `src/youyou/` 仅用于兼容 uv 的包管理，实际代码在 `src/` 下
- 导入时直接使用 `from config import ...`，`from agents.xxx import ...`

## 项目规范

### 文件组织规则
- **根目录只允许**: `README.md` 和 `CLAUDE.md`
- **测试脚本**: 所有 `test_*.py`、`check_*.py` 必须放在 `scripts/` 目录
- **其他文档**: 除 README.md 和 CLAUDE.md 外，其他 .md 文件不允许出现在根目录

项目已配置 post-response hook (`.claude/hooks/post-response.sh`) 自动检查这些规范。

## 开发命令

### 依赖管理
```bash
# 安装/同步依赖
uv sync

# 安装开发依赖
uv sync --all-extras
```

### 运行应用
```bash
# 启动服务端（Flask HTTP 服务，监听 8000 端口）
uv run youyou-server

# 启动客户端（CLI 交互界面）
uv run youyou
```

### 测试
```bash
# 运行所有测试
uv run python -m pytest tests/

# 运行单个测试文件
uv run python -m pytest tests/test_basic.py

# 快速导入测试
uv run python tests/test_basic.py
```

### 代码质量
```bash
# 代码格式化
uv run black src/

# 代码检查
uv run ruff check src/
```

## 核心架构

### 多 Agent 系统
采用 Supervisor-Worker 模式，三层 Agent 架构：

1. **Supervisor Agent** (`agents/supervisor/`)
   - 使用 `ROUTER_MODEL` 进行意图识别和路由
   - 通过 LangChain 1.0 的 `create_agent` 创建
   - **重要**：必须传入 `ChatOpenAI` 实例，而不是字符串格式的模型名
   - 调用两个子 Agent 工具：`item_agent_tool` 和 `chat_agent_tool`

2. **ItemAgent** (`agents/item_agent/`)
   - 使用 `AGENT_MODEL` 处理物品位置相关任务
   - 提供工具：`remember_item_location`、`query_item_location`、`list_all_items`
   - 使用 mem0 进行语义记忆存储

3. **ChatAgent** (`agents/chat_agent/`)
   - 使用 `AGENT_MODEL` 处理普通对话
   - 无需外部工具，纯对话能力

### 记忆系统 (`core/memory.py`)
基于 mem0 和 Qdrant 的向量存储：
- **MemoryManager** 类：封装所有记忆操作
- 延迟初始化设计：`_ensure_initialized()` 在首次使用时初始化
- 数据存储在 `{DATA_DIR}/qdrant/` 目录
- 配置项：
  - `llm`: 使用 `AGENT_MODEL` 进行记忆提取和总结
  - `embedder`: 使用 `EMBEDDING_MODEL` 生成向量
  - `vector_store`: 使用本地 Qdrant

### 客户端-服务端架构
- **服务端** (`server.py`): Flask HTTP 服务
  - `/health`: 健康检查
  - `/chat`: 处理对话请求（POST JSON）
  - `/config`: 获取配置信息
- **客户端** (`cli.py`): 基于 prompt-toolkit 和 rich 的 CLI 界面
  - 发送 HTTP 请求到本地服务端
  - 支持命令：`/help`、`/exit`、`/clear`、`/config`

## 配置管理

### 环境变量 (`.env`)
必须先复制 `.env.example` 并配置：
```bash
OPENAI_API_BASE=https://api.siliconflow.cn/v1  # 或其他兼容 OpenAI 的端点
OPENAI_API_KEY=your_api_key_here
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
USER_ID=default
DATA_DIR=./data
```

### Config 类 (`config.py`)
- 从环境变量加载配置
- 提供 `validate()` 方法验证配置完整性
- 自动创建 `DATA_DIR` 目录

## 数据存储

所有数据存储在 `DATA_DIR`（默认 `./data/`）：
- `qdrant/`: 向量数据库存储
- 此目录会自动创建，不需要手动创建

## LangChain 1.0 特性

项目使用 LangChain 1.0 API：
- **Agent 创建**: 使用 `langchain.agents.create_agent()` 而非旧版 API
- **模型格式**: **必须传入 `ChatOpenAI` 实例**，不能使用字符串格式！
  ```python
  from langchain_openai import ChatOpenAI

  model = ChatOpenAI(
      model=config.AGENT_MODEL,
      base_url=config.OPENAI_API_BASE,
      api_key=config.OPENAI_API_KEY,
      temperature=0
  )

  agent = create_agent(
      model=model,  # 传入实例，不是字符串
      tools=[...],
      system_prompt="..."
  )
  ```
- **工具定义**: 使用 `@tool` 装饰器定义工具函数
- **系统提示**: 通过 `system_prompt` 参数传递

## 常见开发任务

### 添加新 Agent
1. 在 `src/agents/` 创建新目录
2. 创建 `agent.py`（使用 `create_agent`）、`tools.py`（定义工具）、`prompts.py`（系统提示）
3. 在 Supervisor 的 `tools.py` 中添加调用新 Agent 的工具
4. 更新 Supervisor 的系统提示，说明何时使用新 Agent

### 添加新工具
1. 在对应 Agent 的 `tools.py` 中使用 `@tool` 装饰器定义
2. 将工具添加到 Agent 的 `create_agent()` 调用中
3. 更新 Agent 的系统提示，说明如何使用新工具

### 调试记忆系统
记忆系统初始化日志以 `[记忆系统]` 开头，包含：
- Qdrant 路径
- 使用的 LLM 和嵌入模型
- API Base URL
- 初始化成功/失败状态



# 重要规则
- 所有的test脚本必须放在scripts目录下。
