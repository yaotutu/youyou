# NoteAgent 使用指南

## 📝 概述

NoteAgent 是 YouYou 的笔记本 Agent，负责知识存储和检索。它可以：

- 💡 **保存笔记**：记录灵感、想法、文章摘要等
- 🔗 **GitHub 项目分析**：自动爬取和分析 GitHub 项目
- 🔍 **智能搜索**：混合关键词和语义搜索，快速找到笔记
- 🏷️ **自动标签**：使用 LLM 自动提取关键标签
- 📊 **知识中枢**：作为数据存储中枢，其他 Agent 可以调用

## 🏗️ 架构设计

### 存储层
- **SQLite**：存储结构化数据（标题、内容、元数据等）
- **Qdrant**：存储向量，支持语义搜索
- 路径：`{DATA_DIR}/notes/`

### 笔记类型
- `inspiration`: 灵感/想法
- `github_project`: GitHub 项目
- `video_summary`: 视频摘要（未来扩展）
- `article`: 文章笔记
- `link`: 链接收藏
- `other`: 其他

### 核心模块

```
note_agent/
├── storage.py          # 存储层（SQLite + Qdrant）
├── github_analyzer.py  # GitHub 爬虫和分析
├── utils.py            # 自动标签提取和向量生成
├── tools.py            # 工具函数定义
├── prompts.py          # 系统提示
└── agent.py            # Agent 主文件
```

## 🏷️ 标记系统（推荐使用）

NoteAgent 支持**标记路由**，可以明确指定消息交给 NoteAgent 处理，避免 Supervisor 路由错误。

### 支持的标记

| 标记 | 说明 | 示例 |
|------|------|------|
| `#note` | 保存笔记（英文） | `#note 这是一个想法` |
| `#笔记` | 保存笔记（中文） | `#笔记 记录这个知识点` |
| `/note` | 保存笔记（斜杠格式） | `/note 学习笔记` |
| `/笔记` | 保存笔记（斜杠中文） | `/笔记 Python 技巧` |
| `#github` | 分析 GitHub 项目（可选） | `#github https://github.com/...` |
| **GitHub URL** | **自动识别**（推荐） | `https://github.com/...` |

### 标记路由的优势

✅ **明确性**：清楚知道消息会被如何处理
✅ **可靠性**：100% 准确，不依赖意图识别
✅ **效率**：跳过 Supervisor 路由，直接处理
✅ **灵活性**：可选择使用标记或依赖自动路由

### 使用建议

1. **明确保存笔记时**：使用 `#note` 或 `#笔记` 标记
2. **分享 GitHub 项目时**：直接发送 URL，会自动识别
3. **不确定时**：不加标记，让 Supervisor 智能路由

## 🚀 使用示例

### 1. 使用标记保存笔记（推荐）

```bash
# 使用 #note 标记
用户: "#note Python 的装饰器可以用来实现缓存、日志记录、权限验证等功能"

# 使用中文标记
用户: "#笔记 Rust 的所有权系统可以防止数据竞争"

# 使用斜杠格式
用户: "/note 学习了 React Hooks 的使用方法"
```

**效果**：
- ⚡ 直接路由到 NoteAgent（跳过 Supervisor）
- 自动提取标签：`["Python", "装饰器", "缓存"]`
- 生成向量用于语义搜索
- 保存到 SQLite 和 Qdrant

### 2. 不使用标记（依赖智能路由）

```bash
用户: "记一下：Python 的装饰器很强大"
```

**说明**：Supervisor 会尝试识别意图并路由到 NoteAgent，但不如使用标记可靠

### 2. 分析 GitHub 项目

```python
用户: "分析这个项目：https://github.com/langchain-ai/langchain"
```

**效果**：
- 爬取 README 和元数据（Star、Fork、语言等）
- 使用 LLM 提取：
  - 技术栈：`["Python", "LangChain", "OpenAI"]`
  - 项目用途
  - 核心功能
  - 适用场景
- 自动生成结构化笔记并保存

### 3. 搜索笔记（混合模式）

```python
用户: "我之前收藏的 FastAPI 项目在哪？"
```

**搜索策略**：
1. **关键词匹配**：在标题、内容、标签中搜索 "FastAPI"
2. **语义搜索**：如果关键词搜索结果不足，使用向量搜索理解意图

### 4. 列出笔记

```python
# 列出所有笔记
用户: "列出我的所有笔记"

# 按类型过滤
用户: "列出所有 GitHub 项目笔记"
```

### 5. 查看笔记详情

```python
用户: "查看笔记 abc123 的详细内容"
```

## 🔧 工具函数

### save_note
保存笔记

**参数**：
- `title`: 笔记标题
- `content`: 笔记内容
- `note_type`: 笔记类型（可选，默认 `other`）
- `tags`: 标签列表（可选，不提供则自动提取）
- `metadata`: 附加元数据（可选）

### analyze_github_project
分析 GitHub 项目并保存

**参数**：
- `github_url`: GitHub 项目 URL
- `custom_tags`: 自定义标签（可选）

**支持的 URL 格式**：
- `https://github.com/owner/repo`
- `github.com/owner/repo`
- `owner/repo`

### search_notes
搜索笔记

**参数**：
- `query`: 搜索查询
- `note_type`: 笔记类型过滤（可选）
- `limit`: 返回结果数量（默认 5）

**搜索模式**：
- 先关键词搜索
- 关键词不足则补充语义搜索

### list_notes
列出笔记

**参数**：
- `note_type`: 笔记类型过滤（可选）
- `limit`: 返回结果数量（默认 10）

### get_note_detail
获取笔记详情

**参数**：
- `note_id`: 笔记 ID

## 🎯 最佳实践

### 1. GitHub 项目收藏流程

当你看到喜欢的 GitHub 项目时：

```
用户: "https://github.com/fastapi/fastapi"
NoteAgent: [自动分析] FastAPI 是一个现代、高性能的 Python Web 框架...
            技术栈: Python, FastAPI, Pydantic
            已保存为笔记！
```

后续查找：

```
用户: "我之前看的那个高性能 Python Web 框架"
NoteAgent: [语义搜索] 找到了！FastAPI 项目...
```

### 2. 灵感记录

```
用户: "记一下：可以用 Redis 实现分布式锁来解决并发问题"
NoteAgent: ✅ 已保存！标签: [Redis, 分布式, 锁]
```

### 3. 作为知识中枢

未来其他 Agent（如 VideoAgent）完成任务后可以调用 NoteAgent：

```python
# VideoAgent 分析完视频后
from youyou.agents.note_agent.tools import save_note

save_note(
    title="[视频] 深入理解 Docker 容器",
    content="核心要点：1. 容器隔离原理...",
    note_type="video_summary",
    metadata={"url": "...", "duration": "15:30"}
)
```

## 📊 数据结构

### 笔记数据

```python
{
    "id": "abc123",              # 基于内容的哈希
    "type": "github_project",    # 笔记类型
    "title": "[GitHub] langchain-ai/langchain",
    "content": "## langchain-ai/langchain\n...",
    "metadata": {
        "url": "https://github.com/langchain-ai/langchain",
        "stars": 50000,
        "tech_stack": ["Python", "AI"],
        ...
    },
    "tags": ["Python", "AI", "LangChain"],
    "created_at": "2025-11-06T10:30:00",
    "updated_at": "2025-11-06T10:30:00"
}
```

## 🔮 未来扩展

### 已规划功能

1. **视频分析集成**
   - VideoAgent 分析视频后自动保存摘要
   - 支持 YouTube、Bilibili 等平台

2. **文章笔记**
   - 爬取网页文章并提取关键信息
   - 自动生成摘要

3. **笔记导出**
   - 导出为 Markdown
   - 导出为 PDF
   - 导出到 Notion、Obsidian 等

4. **笔记关联**
   - 自动发现笔记之间的关联
   - 构建知识图谱

### 扩展示例

添加新的笔记类型：

```python
# storage.py
class NoteType(str, Enum):
    # ... 现有类型
    BOOK_SUMMARY = "book_summary"  # 新增：书籍摘要
```

## 🛠️ 测试

运行测试脚本：

```bash
uv run python scripts/test_note_agent.py
```

## 📝 注意事项

1. **GitHub API 限制**
   - 未认证：60 次/小时
   - 认证：5000 次/小时
   - 建议添加 GitHub Token（未来支持）

2. **向量维度**
   - 当前使用 `Qwen3-Embedding-8B`，维度 1024
   - 更换嵌入模型需要重建向量索引

3. **递归限制**
   - Agent 默认最大递归 25 次
   - 复杂任务可能需要增加限制

4. **数据持久化**
   - SQLite 数据库：`{DATA_DIR}/notes/notes.db`
   - Qdrant 向量库：`{DATA_DIR}/notes/qdrant/`
   - 建议定期备份

## 🤝 与其他 Agent 的协作

NoteAgent 作为知识中枢，其他 Agent 可以通过调用工具函数来保存数据：

```python
from youyou.agents.note_agent.tools import save_note

# 任何 Agent 都可以调用
save_note(
    title="我的笔记",
    content="笔记内容",
    note_type="other",
    metadata={"source": "VideoAgent"}
)
```

---

**提示**：NoteAgent 的目标是让你轻松保存和找回任何知识！
