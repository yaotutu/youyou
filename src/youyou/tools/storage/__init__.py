"""存储相关通用工具

提供笔记存储、向量搜索等功能，
可被任何 Agent 使用。
"""

from youyou.tools.storage.note_storage import NoteStorage, Note, NoteType
from youyou.tools.storage.utils import NoteUtils

__all__ = ["NoteStorage", "Note", "NoteType", "NoteUtils"]
