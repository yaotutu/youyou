# GitHub 项目检索指南

## 概述

GitHub 项目保存为笔记后，你可以通过多种方式检索它们。系统支持 **混合搜索**（关键词 + 语义），能够智能理解你的搜索意图。

---

## 搜索方式

### 1. 按项目名称搜索

**直接说项目名**：
```
我之前收藏的 FastAPI 在哪？
```

**搜索原理**：
- 匹配 title: `[GitHub] fastapi/fastapi`
- 匹配 tags: `["FastAPI", ...]`

**返回结果**：
```
🔍 搜索结果（关键词匹配，共 1 条）

1. **[GitHub] fastapi/fastapi**
   类型: github_project | 标签: Python, FastAPI, async
   预览: FastAPI 是一个现代、高性能的 Web 框架...
   ID: 81ba8b67-a3d2-5503-a8c5-79589384484f
```

---

### 2. 按技术栈搜索

**搜索特定技术**：
```
查找关于 Python 的项目
搜索 TypeScript 项目
我收藏了哪些 React 相关的项目？
```

**搜索原理**：
- 匹配 tags: `["Python", "React", ...]`
- 匹配 metadata.tech_stack: `["Python", "FastAPI", ...]`
- 匹配 content 中的技术名称

**示例**：
```
搜索 async Python
```

会找到所有标签或内容中包含 "async" 和 "Python" 的项目。

---

### 3. 按功能特性搜索（语义搜索）

**描述你想要的功能**：
```
我想找一个高性能的 API 框架
我需要一个支持异步的 Web 框架
有没有轻量级的数据库工具？
```

**搜索原理**：
- 使用语义向量搜索
- 理解"高性能"、"异步"、"轻量级"等概念
- 不需要精确匹配关键词

**示例**：
```
查询: "我想找个快速的 Python Web 框架"
结果: FastAPI（即使没有"快速"这个词，但语义相关：高性能、Python、Web框架）
```

---

### 4. 按类型过滤

**只看 GitHub 项目**：
```
列出所有 GitHub 项目
列出我的 GitHub 笔记
```

**搜索原理**：
- 过滤 `note_type = "github_project"`

**返回结果**：
```
📚 笔记列表 (共 5 条)

1. **[GitHub] fastapi/fastapi**
   类型: github_project | 标签: Python, FastAPI
   ID: 81ba8b67...
   创建时间: 2025-11-06

2. **[GitHub] langchain-ai/langchain**
   类型: github_project | 标签: Python, AI
   ID: 92cd9c78...
   创建时间: 2025-11-05

...
```

---

### 5. 按 Stars 或热度搜索（高级）

**找最受欢迎的项目**：
```
我收藏的项目中哪个 Star 最多？
找一个很火的 Python 框架
```

**搜索原理**：
- 查询 metadata.stars 字段
- LLM 理解"最多"、"很火"的意图
- 排序返回

---

### 6. 按特定 URL 搜索

**找特定仓库**：
```
我之前保存的 https://github.com/fastapi/fastapi 在哪？
```

**搜索原理**：
- 匹配 metadata.url 或 metadata.original_url

---

## 搜索优化建议

### ✅ 好的搜索方式

| 查询 | 为什么好 | 能找到 |
|------|---------|--------|
| `我之前收藏的 FastAPI` | 明确的项目名 | ✅ FastAPI 项目 |
| `查找 Python Web 框架` | 清晰的技术栈 + 类别 | ✅ FastAPI, Django, Flask... |
| `我想找个支持异步的框架` | 语义清晰 | ✅ FastAPI, aiohttp... |
| `列出所有 GitHub 项目` | 明确类型过滤 | ✅ 所有 GitHub 笔记 |

### ❌ 可以改进的查询

| 查询 | 问题 | 改进 |
|------|------|------|
| `那个项目` | 太模糊 | → `FastAPI 项目` |
| `框架` | 范围太广 | → `Python Web 框架` |
| `快的` | 缺少上下文 | → `高性能的 API 框架` |

---

## 搜索示例

### 场景 1：回忆某个具体项目

**问题**：我记得收藏了一个 FastAPI 的项目，但忘了具体 URL

**搜索**：
```
我之前收藏的 FastAPI 项目
```

**结果**：
```
找到 1 个项目
- [GitHub] fastapi/fastapi
- URL: https://github.com/fastapi/fastapi
- Stars: 91,570
```

---

### 场景 2：找某类技术的项目

**问题**：我想看看之前收藏了哪些 Python 相关的项目

**搜索**：
```
列出所有 Python 项目
```

**结果**：
```
找到 5 个项目
1. FastAPI - Python Web 框架
2. LangChain - Python AI 框架
3. Pydantic - Python 数据验证
...
```

---

### 场景 3：按功能需求查找

**问题**：我需要一个高性能的 API 框架，之前好像收藏过

**搜索**：
```
我想找个高性能的 API 框架
```

**系统理解**：
- "高性能" → 语义向量 → FastAPI (metadata: 高性能)
- "API 框架" → 关键词 → FastAPI (tags: API, 框架)

**结果**：
```
找到匹配项目
- FastAPI (最匹配)
- Flask (次匹配)
```

---

### 场景 4：技术选型参考

**问题**：我要做一个异步项目，看看之前收藏了哪些支持异步的框架

**搜索**：
```
查找支持异步的 Python 框架
```

**结果**：
```
找到相关项目
1. FastAPI (tags: async, Python)
2. aiohttp (tags: async, Python)
```

---

## metadata 中的可搜索字段

GitHub 项目笔记包含丰富的 metadata，都可以用于搜索：

```json
{
  "url": "https://github.com/fastapi/fastapi",
  "stars": 91570,
  "forks": 7862,
  "language": "Python",
  "topics": ["api", "async", "framework"],
  "tech_stack": ["Python", "FastAPI", "Starlette", "Pydantic"],
  "license": "MIT",
  "resource_type": "repo",
  "resource_path": null,
  "original_url": "https://github.com/fastapi/fastapi"
}
```

**可搜索的维度**：
- 项目名称：`fastapi/fastapi`
- Star 数：`91570`（可以找"最火的"）
- 语言：`Python`
- 主题：`api`, `async`, `framework`
- 技术栈：`FastAPI`, `Starlette`, `Pydantic`
- 许可证：`MIT`

---

## 高级搜索技巧

### 1. 组合搜索

```
查找 Python Web 框架，并且 Star 数超过 50000
```

系统会：
1. 关键词搜索：`Python` + `Web` + `框架`
2. LLM 理解：过滤 stars > 50000

### 2. 排除搜索

```
查找 Python 项目，但不是 AI 相关的
```

系统会：
1. 搜索 `Python` 项目
2. 排除包含 `AI`、`Machine Learning` 等标签的项目

### 3. 时间范围

```
列出我最近一周收藏的 GitHub 项目
```

系统会：
1. 过滤 `note_type = github_project`
2. 过滤 `created_at > 7 天前`

---

## 搜索性能

### 关键词搜索（极快）
- 延迟：< 50ms
- 适用：精确查询

### 语义搜索（快）
- 延迟：< 500ms
- 适用：模糊查询、概念查询

### 混合搜索（智能）
- 延迟：< 1 秒
- 先尝试关键词，不足再补充语义
- 99% 情况下能找到你想要的

---

## 常见问题

### Q1: 为什么搜索 "fastapi" 没找到？

**可能原因**：
1. 笔记还没保存成功
2. 拼写错误（检查大小写）
3. 使用了缩写（试试全名 "FastAPI"）

**解决方案**：
```
# 先列出所有 GitHub 项目
列出我的所有 GitHub 项目

# 然后查看是否存在
```

### Q2: 搜索结果太多怎么办？

**添加更多限定条件**：
```
# 太泛
查找 Python 项目

# 更精确
查找 Python Web 框架，并且支持异步
```

### Q3: 搜索结果太少怎么办？

**放宽搜索条件**：
```
# 太严格
查找 Python 3.11 的异步 Web 框架

# 更宽泛
查找 Python 异步框架
```

### Q4: 如何查看项目详情？

**两步操作**：
```
# 第一步：搜索
我之前收藏的 FastAPI

# 第二步：查看详情（使用返回的 ID）
查看笔记 81ba8b67-a3d2-5503-a8c5-79589384484f
```

---

## 总结

### ✅ 已支持

- ✅ 关键词搜索（项目名、技术栈、标签）
- ✅ 语义搜索（理解意图和概念）
- ✅ 混合搜索（自动选择最优策略）
- ✅ 类型过滤（只看 GitHub 项目）
- ✅ metadata 搜索（Stars、语言、主题等）

### 🎯 推荐用法

1. **优先使用具体名称**："FastAPI 项目"
2. **善用技术栈过滤**："Python Web 框架"
3. **描述功能需求**："高性能 API 框架"
4. **先列出再筛选**："列出所有 GitHub 项目"

### 📝 记住

- GitHub 项目 = 笔记的一种类型
- 所有笔记搜索方式都适用于 GitHub 项目
- 系统会自动选择最优搜索策略
- 不需要记住精确的 URL 或 ID，自然语言描述即可

---

**最后建议**：多尝试不同的搜索方式，系统会越来越理解你的搜索习惯！
