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
采用 Supervisor-Worker 模式，多 Agent 架构：

1. **Supervisor Agent** (`agents/supervisor/`)
   - 使用 `ROUTER_MODEL` 进行意图识别和路由
   - 通过 LangChain 1.0 的 `create_agent` 创建
   - **重要**：必须传入 `ChatOpenAI` 实例，而不是字符串格式的模型名
   - 调用子 Agent 工具：`item_agent_tool`、`chat_agent_tool`、`note_agent_tool`、`calendar_agent_tool`

2. **ItemAgent** (`agents/item_agent/`)
   - 使用 `AGENT_MODEL` 处理物品位置相关任务
   - 提供工具：`remember_item_location`、`query_item_location`、`list_all_items`
   - 使用 mem0 进行语义记忆存储

3. **ChatAgent** (`agents/chat_agent/`)
   - 使用 `AGENT_MODEL` 处理普通对话
   - 无需外部工具，纯对话能力

4. **NoteAgent** (`agents/note_agent/`)
   - 使用 `AGENT_MODEL` 处理笔记和知识管理
   - 提供工具：保存笔记、搜索笔记、分析 GitHub 项目
   - 使用 Qdrant 向量库和 SQLite 数据库

5. **CalendarAgent** (`agents/calendar_agent/`)（新增）
   - 使用 `AGENT_MODEL` 处理日历提醒相关任务
   - 提供工具：`add_calendar_reminder`、`list_upcoming_reminders`、`delete_calendar_reminder`
   - 基于 CalDAV 协议，支持 iCloud、Google Calendar 等主流日历服务
   - 使用 LLM 进行自然语言时间解析

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
  - `/docs`: Swagger UI 交互式文档
  - `/api/v1/chat/message`: 处理对话请求（POST JSON）
  - `/api/v1/system/config`: 获取配置信息
  - `/api/v1/system/health`: 健康检查
  - 端口占用处理：服务启动时自动检测并终止占用 8000 端口的进程
- **客户端** (`cli.py`): 基于 prompt-toolkit 和 rich 的 CLI 界面
  - 发送 HTTP 请求到本地服务端
  - 支持命令：`/help`、`/exit`、`/clear`、`/config`

### 结构化响应系统 (`core/response_types.py`)
项目采用统一的结构化响应格式，支持丰富的客户端 UI 渲染（卡片、提醒、笔记等）。

**核心设计原则**：
- **工具返回 dict**：所有 Agent 工具返回包含 `action_type`、`data`、`message` 的字典
- **LangChain 自动序列化**：LangChain 将工具返回的 dict 序列化为 ToolMessage 中的 JSON
- **BaseAgent 提取结构化数据**：从 ToolMessage 中提取所有 action，构建 AgentResponse
- **API 返回统一格式**：所有路由返回相同的结构化 JSON，便于客户端解析

**数据结构**：
```python
@dataclass
class Action:
    type: ActionType  # reminder_set, item_remembered, note_saved, chat_response 等
    data: Dict[str, Any]  # 行为相关的结构化数据

@dataclass
class AgentResponse:
    success: bool
    agent: str
    message: str
    actions: List[Action]
    timestamp: str
    error: Optional[str] = None
```

**工具返回格式**（示例）：
```python
@tool
def remember_item_location(item: str, location: str) -> dict:
    # ... 业务逻辑 ...
    return {
        "action_type": "item_remembered",
        "data": {
            "item": "钥匙",
            "location": "客厅桌上",
            "action": "created"
        },
        "message": "✅ 新记录成功：钥匙 已记录在 客厅桌上"
    }
```

**API 响应格式**：
```json
{
  "success": true,
  "agent": "item_agent",
  "message": "已记录物品位置",
  "timestamp": "2025-11-07T21:23:15.781677",
  "actions": [
    {
      "type": "item_remembered",
      "data": {
        "item": "钥匙",
        "location": "客厅桌上",
        "action": "created"
      }
    },
    {
      "type": "chat_response",
      "data": {
        "text": "✅ 新记录成功：钥匙 已记录在 客厅桌上"
      }
    }
  ]
}
```

**支持的 ActionType**：
- `reminder_set`: 提醒已设置
- `reminder_list`: 提醒列表
- `item_remembered`: 物品已记录
- `item_location`: 物品位置查询结果
- `item_list`: 物品列表
- `note_saved`: 笔记已保存
- `note_list`: 笔记列表
- `chat_response`: 普通对话响应
- `error`: 错误信息

**BaseAgent 处理流程**：
1. Agent 调用工具，工具返回 dict
2. LangChain 将 dict 序列化到 ToolMessage
3. `_extract_response_from_result()` 遍历所有 ToolMessage，提取 action
4. 如果没有 action，默认添加 `chat_response` action
5. 返回包含所有 actions 的 AgentResponse

**测试**：
```bash
# 快速测试结构化响应系统
uv run python scripts/test_structured_response_quick.py
```

### 路由系统
项目使用三层路由机制，优先级从高到低：

1. **标记路由** (`core/tag_parser.py`)
   - 显式标记直接路由，跳过 Supervisor
   - NoteAgent 标记：`#note`、`#笔记`、`/note`、`/笔记`
   - GitHub URL 自动识别

2. **关键词路由** (`core/keyword_router.py`)
   - 基于关键词快速路由，无需 LLM 调用
   - CalendarAgent 关键词：提醒、日历、日程、时间表达式等
   - 提高响应速度和准确率

3. **Supervisor 路由**
   - 使用 `ROUTER_MODEL` 进行意图识别
   - 处理其他未被标记/关键词匹配的请求

### Zep 全局记忆系统 (`core/zep_memory.py`)
基于 Zep 3.0 API 的全局记忆中枢：
- 支持 Zep Cloud 和本地部署两种模式
- 延迟初始化设计：首次使用时自动初始化
- 记录所有用户-助手交互
- 提供语义搜索能力
- 配置项：
  - Cloud 模式：需要 `ZEP_API_KEY` 环境变量
  - 本地模式：使用 `ZEP_API_URL`（默认 http://localhost:8000）

### 会话历史管理 (`core/session_history.py`)
内存级会话历史缓存，减少远程调用：
- 首次访问从 Zep 加载历史
- 后续请求使用内存缓存
- 支持定期刷新策略
- 异步写入 Zep 持久化
- 可配置最大历史长度和刷新间隔

## 配置管理

### 环境变量 (`.env`)
必须先复制 `.env.example` 并配置：

**必需配置**：
```bash
# OpenAI API 配置（兼容 OpenAI 格式的任何端点）
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_API_KEY=your_api_key_here

# 模型配置
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus  # 用于意图路由
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus   # 用于 Agent 处理
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B              # 用于向量嵌入

# 系统配置
USER_ID=default  # 用户标识
DATA_DIR=./data  # 数据存储目录
```

**可选配置**：
```bash
# Zep 记忆系统（二选一）
ZEP_API_KEY=your_zep_cloud_api_key        # Zep Cloud 模式
# 或
ZEP_API_URL=http://localhost:8000         # 本地部署模式

# CalDAV 日历配置（用于 CalendarAgent）
CALDAV_URL=https://caldav.icloud.com      # CalDAV 服务器地址
CALDAV_USERNAME=your_email@example.com    # 用户名（通常是邮箱）
CALDAV_PASSWORD=your_app_specific_password # 密码（建议使用专用密码）
CALDAV_CALENDAR_NAME=YouYou 提醒          # 默认日历名称（可选）
CALDAV_DEFAULT_REMINDER_MINUTES=10        # 默认提醒时间（分钟）
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

### 调试和日志

**日志系统** (`core/logger.py`):
- 基于 `loguru` 实现统一日志管理
- 日志输出到 `logs/youyou_server.log`
- 自动轮转（500MB 大小限制）
- 支持控制台和文件双输出
- 自动拦截标准 logging（Flask 等库）

**日志前缀约定**:
- `[记忆系统]`: ItemAgent 记忆系统日志
- `[Zep记忆]`: Zep 全局记忆日志
- `[会话历史]`: 会话历史管理日志
- `[路由]`: 路由系统日志
- `[NoteAgent]`: 笔记 Agent 日志
- `[CalendarAgent]`: 日历 Agent 日志

**常见调试场景**:
```bash
# 查看实时日志
tail -f logs/youyou_server.log

# 测试特定 Agent（scripts/ 目录下的测试脚本）
uv run python scripts/test_note_agent.py
uv run python scripts/test_calendar_agent.py
uv run python scripts/test_item_agent_tools.py

# 检查数据库状态
uv run python scripts/check_db.py
```

## 工具模块

### NoteAgent 工具 (`tools/storage/`)
- **note_storage.py**: SQLite + Qdrant 双存储
  - 结构化数据存储在 SQLite
  - 向量嵌入存储在 Qdrant
  - 支持混合搜索（关键词 + 语义）
- **utils.py**: 文本处理工具
  - 标签提取
  - 文本摘要
  - 语义去重

### GitHub 工具 (`tools/github/`)
- **analyzer.py**: GitHub 项目分析
  - 自动提取项目元信息（stars、forks、语言等）
  - 解析 README
  - 支持完整 URL 和简写格式（owner/repo）

## 重要规则和约定

### 文件组织
- **所有测试脚本必须放在 `scripts/` 目录**
- 根目录只允许 `README.md` 和 `CLAUDE.md`
- 其他 .md 文件不允许出现在根目录
- 项目配置了 post-response hook 自动检查这些规范

### 导入路径
由于扁平化目录结构，导入时直接使用：
```python
from config import config
from agents.supervisor import supervisor
from core.zep_memory import get_zep_memory
```

### Agent 设计模式
每个 Agent 目录包含：
- `agent.py`: Agent 实现（使用 `create_agent`）
- `tools.py`: 工具函数定义（使用 `@tool` 装饰器）
- `prompts.py`: 系统提示词
- `__init__.py`: 导出接口
