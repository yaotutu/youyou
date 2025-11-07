"""笔记存储层 - 使用 SQLite 和 Qdrant"""
import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import Config


class NoteType(str, Enum):
    """笔记类型"""
    INSPIRATION = "inspiration"  # 灵感/想法
    GITHUB_PROJECT = "github_project"  # GitHub 项目
    VIDEO_SUMMARY = "video_summary"  # 视频摘要
    ARTICLE = "article"  # 文章笔记
    LINK = "link"  # 链接收藏
    OTHER = "other"  # 其他


@dataclass
class Note:
    """笔记数据类"""
    id: str
    type: NoteType
    title: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["type"] = self.type.value
        return data


class NoteStorage:
    """笔记存储管理器"""

    COLLECTION_NAME = "notes"
    VECTOR_SIZE = 4096  # Qwen3-Embedding-8B 实际生成 4096 维向量

    def __init__(self, config: Config):
        self.config = config
        self._initialized = False
        self._db_path: Optional[Path] = None
        self._conn: Optional[sqlite3.Connection] = None
        self._qdrant_client: Optional[QdrantClient] = None

    def _ensure_initialized(self):
        """确保存储已初始化"""
        if self._initialized:
            return

        # 创建数据目录
        notes_dir = Path(self.config.DATA_DIR) / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 SQLite
        self._db_path = notes_dir / "notes.db"
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_database()

        # 初始化 Qdrant（带错误处理）
        qdrant_path = notes_dir / "qdrant"
        qdrant_path.mkdir(exist_ok=True)

        try:
            print(f"[笔记存储] 正在初始化 Qdrant: {qdrant_path}")
            self._qdrant_client = QdrantClient(path=str(qdrant_path))
            self._init_qdrant()
            print(f"[笔记存储] ✓ Qdrant 初始化成功")
        except RuntimeError as e:
            if "already accessed by another instance" in str(e):
                print(f"[笔记存储] ⚠️ Qdrant 已被其他进程占用，向量搜索功能将不可用")
                print(f"[笔记存储] 提示: 关闭其他 youyou-server 进程可解决此问题")
                self._qdrant_client = None  # 设为 None，后续跳过向量操作
            else:
                raise  # 其他错误继续抛出

        self._initialized = True
        print(f"[笔记存储] 初始化完成（向量搜索: {'启用' if self._qdrant_client else '禁用'}）")
        print(f"  - SQLite: {self._db_path}")
        print(f"  - Qdrant: {qdrant_path}")

    def _init_database(self):
        """初始化数据库表"""
        cursor = self._conn.cursor()

        # 创建笔记表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON notes(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON notes(created_at)")

        self._conn.commit()

    def _init_qdrant(self):
        """初始化 Qdrant 集合"""
        collections = self._qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            self._qdrant_client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    def save_note(
        self,
        note_id: str,
        note_type: NoteType,
        title: str,
        content: str,
        metadata: Dict[str, Any],
        tags: List[str],
        vector: Optional[List[float]] = None
    ) -> Note:
        """保存笔记"""
        self._ensure_initialized()

        now = datetime.now().isoformat()

        # 保存到 SQLite
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO notes
            (id, type, title, content, metadata, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note_id,
            note_type.value,
            title,
            content,
            json.dumps(metadata, ensure_ascii=False),
            json.dumps(tags, ensure_ascii=False),
            now,
            now
        ))
        self._conn.commit()

        # 保存向量到 Qdrant（如果可用）
        if vector and self._qdrant_client:
            try:
                self._qdrant_client.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=note_id,
                            vector=vector,
                            payload={
                                "type": note_type.value,
                                "title": title,
                                "tags": tags
                            }
                        )
                    ]
                )
                print(f"[笔记存储] ✓ 向量已保存到 Qdrant")
            except Exception as e:
                print(f"[笔记存储] ⚠️ 向量保存失败: {e}（笔记本身已保存到 SQLite）")
        elif vector:
            print(f"[笔记存储] ⚠️ Qdrant 不可用，跳过向量保存")

        return Note(
            id=note_id,
            type=note_type,
            title=title,
            content=content,
            metadata=metadata,
            tags=tags,
            created_at=now,
            updated_at=now
        )

    def get_note(self, note_id: str) -> Optional[Note]:
        """获取笔记"""
        self._ensure_initialized()

        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Note(
            id=row["id"],
            type=NoteType(row["type"]),
            title=row["title"],
            content=row["content"],
            metadata=json.loads(row["metadata"]),
            tags=json.loads(row["tags"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def search_notes_by_keyword(
        self,
        keyword: str,
        note_type: Optional[NoteType] = None,
        limit: int = 10
    ) -> List[Note]:
        """关键词搜索笔记"""
        self._ensure_initialized()

        cursor = self._conn.cursor()

        if note_type:
            query = """
                SELECT * FROM notes
                WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)
                AND type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            cursor.execute(query, (
                f"%{keyword}%", f"%{keyword}%", f"%{keyword}%",
                note_type.value, limit
            ))
        else:
            query = """
                SELECT * FROM notes
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))

        rows = cursor.fetchall()

        return [
            Note(
                id=row["id"],
                type=NoteType(row["type"]),
                title=row["title"],
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    def search_notes_by_vector(
        self,
        query_vector: List[float],
        note_type: Optional[NoteType] = None,
        limit: int = 10
    ) -> List[Note]:
        """向量搜索笔记"""
        self._ensure_initialized()

        # 构建过滤条件
        filter_dict = None
        if note_type:
            filter_dict = {
                "must": [
                    {"key": "type", "match": {"value": note_type.value}}
                ]
            }

        # 向量搜索
        results = self._qdrant_client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=filter_dict,
            limit=limit
        )

        # 获取完整笔记数据
        notes = []
        for result in results:
            note = self.get_note(str(result.id))
            if note:
                notes.append(note)

        return notes

    def list_notes(
        self,
        note_type: Optional[NoteType] = None,
        limit: int = 20
    ) -> List[Note]:
        """列出笔记"""
        self._ensure_initialized()

        cursor = self._conn.cursor()

        if note_type:
            query = "SELECT * FROM notes WHERE type = ? ORDER BY created_at DESC LIMIT ?"
            cursor.execute(query, (note_type.value, limit))
        else:
            query = "SELECT * FROM notes ORDER BY created_at DESC LIMIT ?"
            cursor.execute(query, (limit,))

        rows = cursor.fetchall()

        return [
            Note(
                id=row["id"],
                type=NoteType(row["type"]),
                title=row["title"],
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                tags=json.loads(row["tags"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        self._ensure_initialized()

        # 从 SQLite 删除
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._conn.commit()

        # 从 Qdrant 删除
        try:
            self._qdrant_client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=[note_id]
            )
        except Exception:
            pass  # 忽略向量不存在的错误

        return cursor.rowcount > 0
