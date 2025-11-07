"""NoteAgent 工具函数

使用通用工具库 (youyou.tools) 提供 Agent 专属的工具接口
"""
import json
from typing import List, Optional

from langchain_core.tools import tool

from config import Config
from tools.storage import NoteStorage, NoteType, NoteUtils
from tools.github import GitHubAnalyzer


# 全局单例实例（模块级别，确保整个进程只有一个实例）
_storage: Optional[NoteStorage] = None
_github_analyzer: Optional[GitHubAnalyzer] = None
_utils: Optional[NoteUtils] = None
_config: Optional[Config] = None


def _get_config() -> Config:
    """获取配置实例（单例）"""
    global _config
    if _config is None:
        _config = Config()
        print("[NoteAgent Tools] 配置加载完成")
    return _config


def _get_storage() -> NoteStorage:
    """获取存储实例（单例）"""
    global _storage
    if _storage is None:
        config = _get_config()
        _storage = NoteStorage(config)
        print("[NoteAgent Tools] 存储实例已创建（单例）")
    return _storage


def _get_github_analyzer() -> GitHubAnalyzer:
    """获取 GitHub 分析器实例（单例）"""
    global _github_analyzer
    if _github_analyzer is None:
        config = _get_config()
        _github_analyzer = GitHubAnalyzer(config)
        print("[NoteAgent Tools] GitHub 分析器已创建（单例）")
    return _github_analyzer


def _get_utils() -> NoteUtils:
    """获取工具实例（单例）"""
    global _utils
    if _utils is None:
        config = _get_config()
        _utils = NoteUtils(config)
        print("[NoteAgent Tools] 工具实例已创建（单例）")
    return _utils


@tool
def save_note(
    title: str,
    content: str,
    note_type: str = "other",
    tags: Optional[List[str]] = None,
    metadata: Optional[dict] = None
) -> str:
    """
    保存笔记

    Args:
        title: 笔记标题
        content: 笔记内容
        note_type: 笔记类型（inspiration/article/link/other 等）
        tags: 标签列表（可选，不提供则自动提取）
        metadata: 附加元数据（可选）

    Returns:
        保存结果消息
    """
    try:
        storage = _get_storage()
        utils = _get_utils()

        # 验证笔记类型
        try:
            nt = NoteType(note_type)
        except ValueError:
            nt = NoteType.OTHER

        # 如果未提供标签，自动提取
        if not tags:
            tags = utils.extract_tags(title, content)

        # 生成笔记 ID
        note_id = utils.generate_note_id(f"{title}:{content}")

        # 生成嵌入向量
        embedding_text = f"{title}\n{content}"
        vector = utils.generate_embedding(embedding_text)

        # 准备元数据
        if metadata is None:
            metadata = {}

        # 保存笔记
        note = storage.save_note(
            note_id=note_id,
            note_type=nt,
            title=title,
            content=content,
            metadata=metadata,
            tags=tags,
            vector=vector if vector else None
        )

        return f"✅ 笔记已保存！\n标题：{title}\n类型：{note_type}\n标签：{', '.join(tags)}\nID：{note_id}"

    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@tool
def analyze_github_project(github_url: str, custom_tags: Optional[List[str]] = None) -> str:
    """
    分析 GitHub 项目并保存为笔记

    Args:
        github_url: GitHub 项目 URL
        custom_tags: 自定义标签（可选）

    Returns:
        分析和保存结果
    """
    try:
        print(f"[analyze_github_project] 开始分析: {github_url}")

        # 步骤 1: 初始化组件
        try:
            analyzer = _get_github_analyzer()
            storage = _get_storage()
            utils = _get_utils()
            print(f"[analyze_github_project] ✓ 组件初始化完成")
        except Exception as e:
            error_msg = f"❌ 初始化失败：{type(e).__name__}: {str(e)}"
            print(f"[analyze_github_project] {error_msg}")
            return error_msg

        # 步骤 2: 分析 GitHub 项目
        print(f"[analyze_github_project] 开始分析项目...")
        result = analyzer.analyze_repo(github_url)

        if not result:
            error_msg = f"❌ 无法分析项目：{github_url}\n请检查 URL 是否正确"
            print(f"[analyze_github_project] {error_msg}")
            return error_msg

        print(f"[analyze_github_project] ✓ GitHub 分析完成: {result['metadata']['full_name']}")

        # 构建标题和内容
        metadata = result["metadata"]
        analysis = result["analysis"]

        title = f"[GitHub] {metadata['full_name']}"

        content_parts = [
            f"## {metadata['full_name']}",
            f"\n**描述**: {metadata['description']}",
            f"\n**语言**: {metadata['language']}",
            f"\n**Stars**: ⭐ {metadata['stars']} | Forks: 🍴 {metadata['forks']}",
            f"\n\n### 项目用途\n{analysis['purpose']}",
        ]

        if analysis['tech_stack']:
            content_parts.append(f"\n\n### 技术栈\n{', '.join(analysis['tech_stack'])}")

        if analysis['key_features']:
            features = '\n'.join([f"- {f}" for f in analysis['key_features']])
            content_parts.append(f"\n\n### 核心功能\n{features}")

        if analysis['use_cases']:
            cases = '\n'.join([f"- {c}" for c in analysis['use_cases']])
            content_parts.append(f"\n\n### 适用场景\n{cases}")

        content = ''.join(content_parts)

        # 生成标签
        auto_tags = []
        if analysis['tech_stack']:
            auto_tags.extend(analysis['tech_stack'][:3])
        if metadata['topics']:
            auto_tags.extend(metadata['topics'][:2])

        # 合并自定义标签
        if custom_tags:
            auto_tags.extend(custom_tags)

        # 去重
        tags = list(set(auto_tags))[:5]

        # 步骤 3: 生成笔记 ID
        note_id = utils.generate_note_id(github_url)
        print(f"[analyze_github_project] ✓ 笔记 ID: {note_id}")

        # 步骤 4: 生成嵌入向量
        print(f"[analyze_github_project] 生成向量...")
        embedding_text = f"{title}\n{analysis['summary']}\n{' '.join(analysis['tech_stack'])}"
        try:
            vector = utils.generate_embedding(embedding_text)
            print(f"[analyze_github_project] ✓ 向量生成完成")
        except Exception as e:
            print(f"[analyze_github_project] ⚠️ 向量生成失败: {e}，将不使用向量")
            vector = None

        # 步骤 5: 准备元数据
        note_metadata = {
            "url": github_url,
            "stars": metadata['stars'],
            "forks": metadata['forks'],
            "language": metadata['language'],
            "topics": metadata['topics'],
            "tech_stack": analysis['tech_stack'],
            "license": metadata['license'],
            # 新增：资源信息
            "resource_type": result.get('resource_info', {}).get('type', 'repo'),
            "resource_path": result.get('resource_info', {}).get('path'),
            "original_url": result.get('resource_info', {}).get('original_url', github_url)
        }

        # 步骤 6: 保存笔记
        print(f"[analyze_github_project] 保存笔记到数据库...")
        try:
            note = storage.save_note(
                note_id=note_id,
                note_type=NoteType.GITHUB_PROJECT,
                title=title,
                content=content,
                metadata=note_metadata,
                tags=tags,
                vector=vector if vector else None
            )
            print(f"[analyze_github_project] ✓ 笔记保存成功")
        except RuntimeError as e:
            if "already accessed by another instance" in str(e):
                error_msg = f"""❌ 数据库访问冲突

**原因**: Qdrant 向量数据库已被其他进程占用（可能是正在运行的服务器）

**解决方案**:
1. 关闭其他正在运行的 youyou-server 进程
2. 或者等待当前操作完成后重试

**项目信息已分析**:
- 项目: {metadata['full_name']}
- Stars: {metadata['stars']}
- 技术栈: {', '.join(analysis['tech_stack'])}

数据未保存，请稍后重试。"""
                print(f"[analyze_github_project] {error_msg}")
                return error_msg
            else:
                raise  # 其他 RuntimeError 继续抛出

        result_msg = f"""✅ GitHub 项目已分析并保存！

📦 **项目**: {metadata['full_name']}
⭐ **Stars**: {metadata['stars']}
🔧 **技术栈**: {', '.join(analysis['tech_stack'])}
🏷️ **标签**: {', '.join(tags)}

💡 **总结**: {analysis['summary']}

📝 **笔记 ID**: {note_id}
"""
        return result_msg

    except Exception as e:
        error_detail = f"❌ 分析失败：{str(e)}"
        print(f"[analyze_github_project] {error_detail}")
        import traceback
        traceback.print_exc()
        return error_detail


@tool
def search_notes(query: str, note_type: Optional[str] = None, limit: int = 5) -> str:
    """
    搜索笔记（混合模式：先关键词，后语义）

    Args:
        query: 搜索查询
        note_type: 笔记类型过滤（可选）
        limit: 返回结果数量

    Returns:
        搜索结果
    """
    try:
        storage = _get_storage()
        utils = _get_utils()

        # 验证笔记类型
        nt = None
        if note_type:
            try:
                nt = NoteType(note_type)
            except ValueError:
                pass

        # 1. 先尝试关键词搜索
        keyword_results = storage.search_notes_by_keyword(
            keyword=query,
            note_type=nt,
            limit=limit
        )

        # 如果关键词搜索找到足够的结果，直接返回
        if len(keyword_results) >= limit:
            return _format_search_results(keyword_results, "关键词匹配")

        # 2. 关键词搜索不足，补充语义搜索
        query_vector = utils.generate_embedding(query)
        if not query_vector:
            # 向量生成失败，只返回关键词结果
            if keyword_results:
                return _format_search_results(keyword_results, "关键词匹配")
            else:
                return "❌ 未找到相关笔记"

        # 语义搜索
        semantic_results = storage.search_notes_by_vector(
            query_vector=query_vector,
            note_type=nt,
            limit=limit
        )

        # 合并结果（去重）
        seen_ids = {note.id for note in keyword_results}
        for note in semantic_results:
            if note.id not in seen_ids:
                keyword_results.append(note)
                seen_ids.add(note.id)
                if len(keyword_results) >= limit:
                    break

        if not keyword_results:
            return "❌ 未找到相关笔记"

        return _format_search_results(keyword_results[:limit], "混合搜索")

    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@tool
def list_notes(note_type: Optional[str] = None, limit: int = 10) -> str:
    """
    列出笔记

    Args:
        note_type: 笔记类型过滤（可选）
        limit: 返回结果数量

    Returns:
        笔记列表
    """
    try:
        storage = _get_storage()

        # 验证笔记类型
        nt = None
        if note_type:
            try:
                nt = NoteType(note_type)
            except ValueError:
                pass

        notes = storage.list_notes(note_type=nt, limit=limit)

        if not notes:
            return "📭 暂无笔记"

        result = f"📚 **笔记列表** (共 {len(notes)} 条)\n\n"

        for i, note in enumerate(notes, 1):
            tags_str = ', '.join(note.tags) if note.tags else '无标签'
            result += f"{i}. **{note.title}**\n"
            result += f"   类型: {note.type.value} | 标签: {tags_str}\n"
            result += f"   ID: {note.id}\n"
            result += f"   创建时间: {note.created_at[:10]}\n\n"

        return result

    except Exception as e:
        return f"❌ 列表获取失败：{str(e)}"


@tool
def get_note_detail(note_id: str) -> str:
    """
    获取笔记详情

    Args:
        note_id: 笔记 ID

    Returns:
        笔记详细内容
    """
    try:
        storage = _get_storage()
        note = storage.get_note(note_id)

        if not note:
            return f"❌ 未找到笔记：{note_id}"

        result = f"""📝 **笔记详情**

**标题**: {note.title}
**类型**: {note.type.value}
**标签**: {', '.join(note.tags) if note.tags else '无'}
**创建时间**: {note.created_at}

---

{note.content}

---

**元数据**:
{json.dumps(note.metadata, ensure_ascii=False, indent=2)}
"""
        return result

    except Exception as e:
        return f"❌ 获取详情失败：{str(e)}"


def _format_search_results(notes: List, search_type: str) -> str:
    """格式化搜索结果"""
    result = f"🔍 **搜索结果** ({search_type}，共 {len(notes)} 条)\n\n"

    for i, note in enumerate(notes, 1):
        tags_str = ', '.join(note.tags) if note.tags else '无标签'

        # 截取内容预览
        content_preview = note.content.replace('\n', ' ')[:100]
        if len(note.content) > 100:
            content_preview += "..."

        result += f"{i}. **{note.title}**\n"
        result += f"   类型: {note.type.value} | 标签: {tags_str}\n"
        result += f"   预览: {content_preview}\n"
        result += f"   ID: {note.id}\n\n"

    return result


# 导出所有工具
def get_note_agent_tools():
    """获取 NoteAgent 的所有工具"""
    return [
        save_note,
        analyze_github_project,
        search_notes,
        list_notes,
        get_note_detail
    ]
