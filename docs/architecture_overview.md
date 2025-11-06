# YouYou 架构总览

## 项目结构

```
youyou/
├── tools/                          # ✨ 通用工具库
│   ├── __init__.py
│   ├── github/                     # GitHub 相关工具
│   │   ├── __init__.py
│   │   └── analyzer.py             # GitHub 项目分析器
│   └── storage/                    # 存储相关工具
│       ├── __init__.py
│       ├── note_storage.py         # 笔记存储（SQLite + Qdrant）
│       └── utils.py                # 存储工具函数
│
├── agents/                         # Agent 层
│   ├── item_agent/                 # 物品位置管理 Agent
│   ├── chat_agent/                 # 对话 Agent
│   └── note_agent/                 # 笔记管理 Agent
│       ├── agent.py                # Agent 主逻辑
│       ├── tools.py                # Agent 专属工具（调用通用工具）
│       └── prompts.py              # System Prompt
│
├── core/                           # 核心模块
│   ├── agent_base.py               # Agent 基类和注册中心
│   └── memory.py                   # 记忆系统（Zep）
│
└── config.py                       # 配置管理
```

## 核心设计理念

### Agent vs Tool

**Agent**（有不确定性）：
- 使用 LLM 进行推理和决策
- 根据用户意图选择工具
- 处理复杂的多步骤任务
- 例如：NoteAgent、ItemAgent、ChatAgent

**Tool**（确定性操作）：
- 输入 → 输出，纯函数/类
- 不使用 LLM（或最小化使用）
- 可被任何 Agent 复用
- 例如：GitHubAnalyzer、NoteStorage

## 通用工具库 (youyou.tools)

### 设计目标
1. **可复用**：任何 Agent 都可以使用
2. **独立性**：不依赖特定 Agent
3. **确定性**：输入输出明确
4. **易测试**：可独立单元测试

### 当前工具

#### 1. GitHub 工具 (`tools.github`)

**GitHubAnalyzer**
- 功能：分析 GitHub 项目
- 输入：GitHub URL（任意格式）
- 输出：项目元数据、README、技术栈分析
- 使用场景：
  - NoteAgent 保存 GitHub 项目
  - 未来的 ResearchAgent 分析开源项目
  - CodeAgent 查找代码示例

**使用示例**：
```python
from youyou.tools.github import GitHubAnalyzer

analyzer = GitHubAnalyzer(config)
result = analyzer.analyze_repo("https://github.com/fastapi/fastapi")
# 返回：{metadata, readme, analysis, resource_info}
```

#### 2. 存储工具 (`tools.storage`)

**NoteStorage**
- 功能：笔记持久化存储
- 数据库：SQLite（结构化） + Qdrant（向量）
- 支持：关键词搜索、语义搜索、混合搜索
- 使用场景：
  - NoteAgent 保存笔记
  - 未来的 VideoAgent 保存视频摘要
  - ResearchAgent 保存研究结果

**NoteUtils**
- 功能：笔记相关工具函数
- 包含：ID 生成、Embedding 生成、标签提取等

**使用示例**：
```python
from youyou.tools.storage import NoteStorage, NoteType

storage = NoteStorage(config)
storage.save_note(
    note_id=note_id,
    note_type=NoteType.GITHUB_PROJECT,
    title="FastAPI",
    content="...",
    metadata={...},
    tags=["Python", "API"],
    vector=[...]  # 可选
)

# 搜索
notes = storage.search_notes_by_keyword("FastAPI")
```

## Agent 层

### Supervisor Agent
- **职责**：路由请求到对应的子 Agent
- **模型**：使用 `ROUTER_MODEL` (DeepSeek-V3.1)
- **工具**：`item_agent_tool`, `chat_agent_tool`, `note_agent_tool`

### NoteAgent
- **职责**：笔记和知识管理
- **功能**：
  - 保存笔记、灵感、想法
  - 分析 GitHub 项目（调用 `tools.github`）
  - 搜索和检索笔记（调用 `tools.storage`）
- **模型**：使用 `AGENT_MODEL`

### ItemAgent
- **职责**：物品位置记忆
- **存储**：mem0 + Qdrant

### ChatAgent
- **职责**：一般性对话
- **特点**：无需外部工具

## 数据流示例

### GitHub 项目保存流程

```
用户: "https://github.com/fastapi/fastapi"
  ↓
Supervisor 路由 → NoteAgent
  ↓
NoteAgent 调用 analyze_github_project 工具
  ↓
工具调用 GitHubAnalyzer (通用工具)
  ↓
GitHubAnalyzer 返回分析结果
  ↓
工具调用 NoteStorage (通用工具)
  ↓
NoteStorage 保存到 SQLite + Qdrant
  ↓
返回成功消息给用户
```

### 笔记搜索流程

```
用户: "给我讲讲 immich"
  ↓
Supervisor 路由 → NoteAgent
  ↓
NoteAgent 调用 search_notes 工具
  ↓
工具调用 NoteStorage (通用工具)
  ↓
NoteStorage 执行混合搜索
  ↓
返回搜索结果
  ↓
NoteAgent 整合结果返回给用户
```

## 配置管理

### 环境变量 (`.env`)
```bash
OPENAI_API_BASE=https://api.siliconflow.cn/v1
OPENAI_API_KEY=your_key
ROUTER_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
AGENT_MODEL=Pro/deepseek-ai/DeepSeek-V3.1-Terminus
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
USER_ID=default
DATA_DIR=./data
```

### Config 类
- 从环境变量加载配置
- 提供配置验证
- 单例模式确保一致性

## 数据存储

```
data/
├── notes/
│   ├── notes.db            # SQLite 数据库
│   └── qdrant/             # Qdrant 向量数据库
└── qdrant/                 # ItemAgent 使用的 Qdrant
```

## 扩展性设计

### 添加新工具

**步骤**：
1. 在 `youyou/tools/` 创建新目录（如 `video/`）
2. 实现工具类（确定性操作）
3. 创建 `__init__.py` 导出
4. 任何 Agent 都可以导入使用

**示例**：
```python
# youyou/tools/video/analyzer.py
class VideoAnalyzer:
    def analyze_video(self, url: str) -> dict:
        # 分析视频内容
        return {...}

# agents/video_agent/tools.py
from youyou.tools.video import VideoAnalyzer
from youyou.tools.storage import NoteStorage

analyzer = VideoAnalyzer(config)
storage = NoteStorage(config)
```

### 添加新 Agent

**步骤**：
1. 在 `youyou/agents/` 创建新目录
2. 实现 Agent（继承 BaseAgent）
3. 导入需要的通用工具
4. 在 Supervisor 中注册

**示例**：
```python
# agents/research_agent/agent.py
from youyou.core.agent_base import BaseAgent
from youyou.tools.github import GitHubAnalyzer
from youyou.tools.storage import NoteStorage

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="research_agent", ...)
        # 使用通用工具
        self.github = GitHubAnalyzer(config)
        self.storage = NoteStorage(config)
```

## 设计优势

### ✅ 清晰的职责分离
- Agent 专注于决策（LLM）
- Tool 专注于执行（确定性）

### ✅ 高度可复用
- 工具可被任何 Agent 使用
- 避免重复实现

### ✅ 易于测试
- 工具可独立测试
- Agent 可 mock 工具

### ✅ 易于扩展
- 新工具不影响现有 Agent
- 新 Agent 可直接使用现有工具

## 最佳实践

### 1. 工具设计原则
- ✅ 单一职责
- ✅ 输入输出明确
- ✅ 无副作用（或副作用可控）
- ✅ 完善的错误处理
- ✅ 详细的日志输出

### 2. Agent 设计原则
- ✅ 明确的职责范围
- ✅ 清晰的 System Prompt
- ✅ 合理使用工具
- ✅ 不要重复实现通用功能

### 3. 代码组织原则
- ✅ 通用功能放在 `tools/`
- ✅ Agent 专属逻辑放在 `agents/xxx/`
- ✅ 核心基础设施放在 `core/`
- ✅ 测试脚本放在 `scripts/`

## 总结

YouYou 采用**分层架构**和**工具复用**设计：

1. **Tools 层**：提供确定性的通用工具
2. **Agent 层**：使用 LLM 进行决策，调用工具完成任务
3. **Core 层**：提供基础设施（Agent 基类、记忆系统等）

这种设计让系统更加**模块化**、**可维护**、**可扩展**！🚀
