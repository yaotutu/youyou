# YouYou 工具架构重构

## 重构日期
2025-11-06

## 重构目标
将 GitHub 分析和笔记存储功能从 NoteAgent 中解耦，作为通用工具库，供所有 Agent 复用。

## 核心理念

### Agent vs Tool
- **Agent**：有不确定性，需要推理和决策（使用 LLM）
- **Tool**：确定性操作，输入 → 输出（纯函数/类）

**GitHub 分析**和**笔记存储**都是确定性操作，应该作为通用工具。

## 新架构

```
youyou/
├── tools/                          # 通用工具库（新增）
│   ├── __init__.py
│   ├── github/                     # GitHub 相关工具
│   │   ├── __init__.py
│   │   └── analyzer.py             # GitHub 分析器（从 note_agent 移动）
│   └── storage/                    # 存储相关工具
│       ├── __init__.py
│       ├── note_storage.py         # 笔记存储（从 note_agent 移动）
│       └── utils.py                # 存储工具函数
│
├── agents/
│   ├── note_agent/
│   │   ├── agent.py                # 不变
│   │   ├── tools.py                # 改为使用 youyou.tools
│   │   └── prompts.py              # 不变
│   ├── item_agent/                 # 可以使用 youyou.tools.storage
│   └── chat_agent/                 # 可以使用任何通用工具
```

## 文件移动

| 原路径 | 新路径 | 说明 |
|--------|--------|------|
| `agents/note_agent/github_analyzer.py` | `tools/github/analyzer.py` | GitHub 分析器 |
| `agents/note_agent/storage.py` | `tools/storage/note_storage.py` | 笔记存储 |
| `agents/note_agent/utils.py` | `tools/storage/utils.py` | 存储工具函数 |

## 导入方式变化

### 旧方式（Agent 内部）
```python
from youyou.agents.note_agent.storage import NoteStorage
from youyou.agents.note_agent.github_analyzer import GitHubAnalyzer
from youyou.agents.note_agent.utils import NoteUtils
```

### 新方式（通用工具）
```python
from youyou.tools.storage import NoteStorage, NoteType, NoteUtils
from youyou.tools.github import GitHubAnalyzer
```

## 使用示例

### 在 NoteAgent 中使用
```python
# agents/note_agent/tools.py
from youyou.tools.storage import NoteStorage, NoteType, NoteUtils
from youyou.tools.github import GitHubAnalyzer

# 使用通用工具
analyzer = GitHubAnalyzer(config)
storage = NoteStorage(config)
utils = NoteUtils(config)
```

### 在未来的其他 Agent 中使用
```python
# agents/video_agent/tools.py
from youyou.tools.storage import NoteStorage, NoteType

# VideoAgent 也可以保存笔记
def save_video_summary():
    storage = NoteStorage(config)
    storage.save_note(...)
```

```python
# agents/research_agent/tools.py
from youyou.tools.github import GitHubAnalyzer

# ResearchAgent 可以分析 GitHub 项目
def analyze_open_source_project(url: str):
    analyzer = GitHubAnalyzer(config)
    result = analyzer.analyze_repo(url)
    return result
```

## 优势

### 1. 代码复用
- ✅ 任何 Agent 都可以使用 GitHub 分析功能
- ✅ 任何 Agent 都可以保存笔记
- ✅ 不需要重复实现相同功能

### 2. 职责分离
- ✅ Agent 专注于决策逻辑（使用 LLM）
- ✅ Tool 专注于确定性操作（纯函数）
- ✅ 架构更清晰

### 3. 易于测试
- ✅ 工具可以独立测试
- ✅ 不依赖特定 Agent
- ✅ 单元测试更简单

### 4. 易于扩展
- ✅ 新 Agent 可以直接使用现有工具
- ✅ 工具改进惠及所有 Agent
- ✅ 添加新工具不影响现有 Agent

## 向后兼容性

✅ **完全向后兼容**

- 旧的导入路径仍然存在（文件还在）
- NoteAgent 的功能完全不变
- 用户体验无任何变化

## 未来扩展

### 可能的新工具
```
youyou/tools/
├── github/          # ✅ 已实现
├── storage/         # ✅ 已实现
├── video/           # 🔮 未来：视频分析工具
├── web/             # 🔮 未来：网页抓取工具
├── embedding/       # 🔮 未来：向量嵌入工具
└── search/          # 🔮 未来：搜索引擎工具
```

### 可能的新 Agent
```
youyou/agents/
├── note_agent/      # ✅ 使用 github + storage
├── item_agent/      # ✅ 可以使用 storage
├── chat_agent/      # ✅ 可以使用任何工具
├── video_agent/     # 🔮 未来：使用 video + storage
├── research_agent/  # 🔮 未来：使用 github + web + storage
└── code_agent/      # 🔮 未来：使用 github + embedding
```

## 迁移指南

如果你在其他地方使用了旧的导入路径，需要更新：

### 步骤 1：更新导入
```python
# 旧
from youyou.agents.note_agent.storage import NoteStorage

# 新
from youyou.tools.storage import NoteStorage
```

### 步骤 2：测试
```bash
uv run python scripts/test_github_vector_fix.py
uv run python scripts/test_immich_query_detailed.py
```

### 步骤 3：清理（可选）
旧文件仍然保留，如果确认无影响，可以删除：
```bash
# 可选：删除旧文件（慎重！）
# rm src/youyou/agents/note_agent/github_analyzer.py
# rm src/youyou/agents/note_agent/storage.py
# rm src/youyou/agents/note_agent/utils.py
```

## 测试结果

✅ **所有测试通过**

- ✅ GitHub 项目分析测试
- ✅ 笔记搜索测试
- ✅ 向量存储测试
- ✅ 意图识别测试

## 总结

这次重构将 GitHub 分析和笔记存储从 NoteAgent 中提取为通用工具：

1. **更好的架构**：Agent 和 Tool 职责分离
2. **更高的复用性**：所有 Agent 都可以使用
3. **更易扩展**：新功能可以独立添加
4. **完全兼容**：不影响现有功能

这是向更模块化、更可维护架构迈进的重要一步！🎉
