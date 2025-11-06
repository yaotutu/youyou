"""标记解析器 - 识别用户消息中的 Agent 路由标记"""
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ParseResult:
    """解析结果"""
    has_tag: bool  # 是否包含标记
    target_agent: Optional[str]  # 目标 Agent 名称
    clean_message: str  # 移除标记后的消息
    original_message: str  # 原始消息
    tag_type: Optional[str]  # 标记类型（note/github/auto）


class TagParser:
    """标记解析器

    支持的标记格式：
    - #note, #笔记, /note, /笔记 - 触发 NoteAgent
    - #github - 分析 GitHub 项目（可选）
    - 自动识别：GitHub URL 自动触发
    """

    # 支持的标记模式
    NOTE_TAGS = [
        r'^#note\s+',  # #note 开头
        r'^#笔记\s+',  # #笔记 开头
        r'^/note\s+',  # /note 开头
        r'^/笔记\s+',  # /笔记 开头
    ]

    GITHUB_TAGS = [
        r'^#github\s+',  # #github 开头
    ]

    # GitHub URL 模式
    GITHUB_URL_PATTERN = r'https?://github\.com/[\w-]+/[\w.-]+|github\.com/[\w-]+/[\w.-]+|^[\w-]+/[\w.-]+$'

    @classmethod
    def parse(cls, message: str) -> ParseResult:
        """
        解析用户消息，识别标记

        Args:
            message: 用户输入的原始消息

        Returns:
            ParseResult 对象
        """
        if not message or not message.strip():
            return ParseResult(
                has_tag=False,
                target_agent=None,
                clean_message=message,
                original_message=message,
                tag_type=None
            )

        message = message.strip()

        # 1. 检测笔记标记（#note, /note 等）
        for pattern in cls.NOTE_TAGS:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                clean_message = message[match.end():].strip()
                return ParseResult(
                    has_tag=True,
                    target_agent="note_agent",
                    clean_message=clean_message,
                    original_message=message,
                    tag_type="note"
                )

        # 2. 检测 GitHub 标记（#github）
        for pattern in cls.GITHUB_TAGS:
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                clean_message = message[match.end():].strip()
                return ParseResult(
                    has_tag=True,
                    target_agent="note_agent",
                    clean_message=clean_message,
                    original_message=message,
                    tag_type="github"
                )

        # 3. 自动识别 GitHub URL
        if cls._contains_github_url(message):
            return ParseResult(
                has_tag=True,
                target_agent="note_agent",
                clean_message=message,  # 保留原始消息
                original_message=message,
                tag_type="auto_github"
            )

        # 4. 没有标记，返回原始消息
        return ParseResult(
            has_tag=False,
            target_agent=None,
            clean_message=message,
            original_message=message,
            tag_type=None
        )

    @classmethod
    def _contains_github_url(cls, message: str) -> bool:
        """
        检测消息是否包含 GitHub URL

        Args:
            message: 用户消息

        Returns:
            是否包含 GitHub URL
        """
        return bool(re.search(cls.GITHUB_URL_PATTERN, message))

    @classmethod
    def extract_github_url(cls, message: str) -> Optional[str]:
        """
        从消息中提取 GitHub URL

        Args:
            message: 用户消息

        Returns:
            提取的 GitHub URL，如果不存在则返回 None
        """
        match = re.search(cls.GITHUB_URL_PATTERN, message)
        if match:
            return match.group(0)
        return None

    @classmethod
    def get_supported_tags(cls) -> Dict[str, str]:
        """
        获取支持的标记列表

        Returns:
            标记说明字典
        """
        return {
            "#note": "保存笔记到 NoteAgent",
            "#笔记": "保存笔记到 NoteAgent（中文）",
            "/note": "保存笔记到 NoteAgent（斜杠格式）",
            "/笔记": "保存笔记到 NoteAgent（斜杠中文格式）",
            "#github": "分析 GitHub 项目（可选，URL 会自动识别）",
            "GitHub URL": "自动识别并分析 GitHub 项目"
        }
