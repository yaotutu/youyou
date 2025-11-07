"""物品数据库管理模块

使用 SQLite 进行精确存储和查询。
"""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import threading


def get_timestamp() -> str:
    """获取当前时间戳 (ISO 8601 with timezone)"""
    return datetime.now(timezone.utc).isoformat()


def normalize_item_name(item: str) -> str:
    """
    规范化物品名称

    规则:
    - 转小写
    - 去除多余空格
    - 去除常见标点符号
    """
    item = item.lower().strip()
    # 去除标点
    item = re.sub(r'[，。！？、；：""''（）《》【】]', '', item)
    # 压缩空格
    item = re.sub(r'\s+', ' ', item)
    return item


def extract_aliases(item: str) -> List[str]:
    """
    从物品名称提取可能的别名

    例如: "笔记本电脑" -> ["笔记本电脑", "笔记本", "电脑", "laptop"]
    """
    aliases = [item]
    normalized = normalize_item_name(item)

    # 常见简称映射
    alias_map = {
        "笔记本电脑": ["电脑", "笔记本", "laptop"],
        "手机": ["电话", "phone"],
        "钥匙": ["key"],
        "护照": ["passport"],
        "身份证": ["id", "身份证件"],
        "充电器": ["充电线", "charger"],
        "耳机": ["headphone", "earphone"],
        "钱包": ["wallet"],
    }

    for key, values in alias_map.items():
        if key in normalized:
            aliases.extend(values)

    # 去重
    return list(set(aliases))


def extract_keywords(text: str) -> List[str]:
    """
    从文本中提取关键词用于模糊搜索

    策略:
    1. 移除常见的助词、介词、量词
    2. 提取2-4个字的词组
    3. 保留单个汉字(长度>=2时)

    例如: "摩托车钥匙" -> ["摩托车", "钥匙", "摩托车钥匙"]
         "摩托车的钥匙" -> ["摩托车", "钥匙", "摩托车的钥匙"]

    Args:
        text: 输入文本

    Returns:
        关键词列表
    """
    # 常见的停用词(助词、介词等)
    stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看'}

    normalized = normalize_item_name(text)
    keywords = []

    # 保留完整文本
    keywords.append(normalized)

    # 移除停用词
    for word in stopwords:
        normalized = normalized.replace(word, ' ')

    # 按空格分割
    parts = normalized.split()
    for part in parts:
        part = part.strip()
        if len(part) >= 2:  # 至少2个字符
            keywords.append(part)

            # 如果是长词,提取子串(2-4字)
            if len(part) > 4:
                for i in range(len(part) - 1):
                    for length in [2, 3, 4]:
                        if i + length <= len(part):
                            substr = part[i:i+length]
                            if len(substr) >= 2:
                                keywords.append(substr)

    # 去重并按长度排序(优先使用长关键词)
    keywords = list(set(keywords))
    keywords.sort(key=len, reverse=True)

    return keywords


class ItemDatabase:
    """物品数据库管理类"""

    def __init__(self, db_path: Path):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()  # 添加线程锁
        self._init_db()

    def _init_db(self):
        """初始化数据库连接和表结构"""
        # 确保目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 连接数据库
        # 使用 WAL 模式支持并发,timeout=30避免锁定超时
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level=None,  # autocommit mode
            timeout=30.0
        )
        self.conn.row_factory = sqlite3.Row

        # 启用 WAL 模式 (Write-Ahead Logging) 支持并发
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        print(f"[数据库] 初始化数据库: {self.db_path}")

        # 创建表结构
        self._create_tables()

        print("[数据库] ✓ 数据库初始化完成")

    def _create_tables(self):
        """创建数据库表结构"""
        cursor = self.conn.cursor()

        # 主表: items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- 物品标识
                item_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                item_aliases TEXT,

                -- 位置信息
                location TEXT NOT NULL,
                location_detail TEXT,

                -- 用户信息
                user_id TEXT NOT NULL DEFAULT 'default',

                -- 时间戳
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                moved_at TEXT,

                -- 统计信息
                move_count INTEGER DEFAULT 0,
                query_count INTEGER DEFAULT 0,

                -- 状态标记
                is_deleted INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,

                -- 额外元数据
                tags TEXT,
                notes TEXT,
                importance INTEGER DEFAULT 0,

                -- 最后访问时间
                last_accessed_at TEXT,

                -- 唯一约束
                UNIQUE(user_id, normalized_name)
            )
        """)

        # 索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_user_normalized
            ON items(user_id, normalized_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_updated_at
            ON items(updated_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_is_deleted
            ON items(is_deleted)
        """)

        # 历史表: item_history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- 关联
                item_id INTEGER NOT NULL,

                -- 快照数据
                item_name TEXT NOT NULL,
                location TEXT NOT NULL,
                location_detail TEXT,

                -- 变更信息
                action TEXT NOT NULL,
                changed_field TEXT,
                old_value TEXT,
                new_value TEXT,

                -- 时间戳
                timestamp TEXT NOT NULL,

                -- 用户信息
                user_id TEXT NOT NULL,

                -- 额外信息
                notes TEXT,

                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_item_id
            ON item_history(item_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp
            ON item_history(timestamp)
        """)

        # FTS5 全文搜索表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                item_name,
                normalized_name,
                item_aliases,
                location,
                tags,
                content='items',
                content_rowid='id'
            )
        """)

        # 触发器: 自动同步 FTS5
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS items_fts_insert
            AFTER INSERT ON items BEGIN
                INSERT INTO items_fts(rowid, item_name, normalized_name, item_aliases, location, tags)
                VALUES (new.id, new.item_name, new.normalized_name, new.item_aliases, new.location, new.tags);
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS items_fts_update
            AFTER UPDATE ON items BEGIN
                UPDATE items_fts
                SET item_name = new.item_name,
                    normalized_name = new.normalized_name,
                    item_aliases = new.item_aliases,
                    location = new.location,
                    tags = new.tags
                WHERE rowid = new.id;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS items_fts_delete
            AFTER DELETE ON items BEGIN
                DELETE FROM items_fts WHERE rowid = old.id;
            END
        """)

        self.conn.commit()

    def _verify_item_name(self, result: Dict[str, Any], query_item: str) -> bool:
        """验证查询结果的物品名称是否匹配查询

        防止记忆混淆:只有当查询词在物品名称中时才认为匹配成功。

        Args:
            result: 数据库查询结果(dict)
            query_item: 用户查询的物品名称

        Returns:
            True 如果匹配, False 如果不匹配

        Examples:
            >>> result = {'item_name': '护照', 'location': '卧室'}
            >>> self._verify_item_name(result, '护照')  # True
            >>> self._verify_item_name(result, '时光机')  # False
        """
        stored_name = result['item_name'].lower().strip()
        query_name = query_item.lower().strip()
        normalized_query = normalize_item_name(query_item)
        normalized_stored = normalize_item_name(result['item_name'])

        # 策略1: 查询词完全包含在物品名称中
        if query_name in stored_name:
            return True

        # 策略2: 物品名称包含在查询词中 (如查询"家门钥匙",匹配"钥匙")
        if stored_name in query_name:
            return True

        # 策略3: 规范化后的名称匹配
        if normalized_query in normalized_stored or normalized_stored in normalized_query:
            return True

        # 策略4: 检查别名
        if 'item_aliases' in result and result['item_aliases']:
            try:
                aliases = json.loads(result['item_aliases'])
                for alias in aliases:
                    alias_lower = alias.lower().strip()
                    if query_name in alias_lower or alias_lower in query_name:
                        return True
            except:
                pass

        return False

    def remember_item(self, item: str, location: str,
                      user_id: str = 'default',
                      location_detail: Optional[str] = None) -> Dict[str, Any]:
        """
        记录物品位置

        处理逻辑:
        - 如果物品已存在且位置相同: 仅更新访问时间
        - 如果物品已存在但位置不同: 更新位置并记录历史
        - 如果物品不存在: 创建新记录

        Args:
            item: 物品名称
            location: 位置
            user_id: 用户ID
            location_detail: 详细位置描述

        Returns:
            包含操作结果的字典
        """
        with self._lock:  # 使用线程锁
            normalized = normalize_item_name(item)
            aliases = extract_aliases(item)
            now = get_timestamp()

            print(f"[数据库] 记录物品: {item} -> {location}")
            print(f"[数据库]   规范化名称: {normalized}")
            print(f"[数据库]   别名: {aliases}")

            cursor = self.conn.cursor()

        # 检查是否已存在
        cursor.execute("""
            SELECT * FROM items
            WHERE user_id = ? AND normalized_name = ? AND is_deleted = 0
        """, (user_id, normalized))

        existing = cursor.fetchone()

        if existing:
            existing_dict = dict(existing)
            print(f"[数据库] 物品已存在, ID: {existing_dict['id']}")

            # 位置相同 -> 仅更新访问时间
            if existing_dict['location'] == location:
                cursor.execute("""
                    UPDATE items
                    SET last_accessed_at = ?,
                        query_count = query_count + 1
                    WHERE id = ?
                """, (now, existing_dict['id']))
                self.conn.commit()

                print(f"[数据库] ✓ 位置相同,仅更新访问时间")
                return {
                    'status': 'success',
                    'action': 'confirmed',
                    'item': item,
                    'location': location,
                    'message': f"{item}确实在{location}"
                }

            # 位置不同 -> 更新位置并记录历史
            else:
                old_location = existing_dict['location']

                cursor.execute("""
                    UPDATE items
                    SET location = ?,
                        location_detail = ?,
                        updated_at = ?,
                        moved_at = ?,
                        move_count = move_count + 1
                    WHERE id = ?
                """, (location, location_detail, now, now, existing_dict['id']))

                # 记录历史
                cursor.execute("""
                    INSERT INTO item_history
                    (item_id, item_name, location, location_detail, action,
                     changed_field, old_value, new_value, timestamp, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (existing_dict['id'], item, location, location_detail,
                      'move', 'location', old_location, location, now, user_id))

                self.conn.commit()

                print(f"[数据库] ✓ 位置已更新: {old_location} -> {location}")
                return {
                    'status': 'success',
                    'action': 'moved',
                    'item': item,
                    'location': location,
                    'old_location': old_location,
                    'new_location': location,
                    'message': f"{item}已从{old_location}移动到{location}"
                }

        # 不存在 -> 创建新记录
        else:
            cursor.execute("""
                INSERT INTO items
                (item_name, normalized_name, item_aliases, location, location_detail,
                 user_id, created_at, updated_at, moved_at, move_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item, normalized, json.dumps(aliases, ensure_ascii=False),
                  location, location_detail, user_id, now, now, now, 0))

            item_id = cursor.lastrowid

            # 记录历史
            cursor.execute("""
                INSERT INTO item_history
                (item_id, item_name, location, location_detail, action,
                 new_value, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, item, location, location_detail,
                  'create', location, now, user_id))

            self.conn.commit()

            print(f"[数据库] ✓ 新建记录, ID: {item_id}")
            return {
                'status': 'success',
                'action': 'created',
                'item': item,
                'location': location,
                'message': f"已记住: {item}在{location}"
            }

    def query_item(self, item: str, user_id: str = 'default') -> Dict[str, Any]:
        """
        查询物品位置 - 四级查询策略

        查询优先级:
        1. 精确匹配 (normalized_name)
        2. 别名匹配 (item_aliases LIKE)
        3. FTS5 全文搜索
        4. LIKE 中文模糊匹配 (关键词子串)

        Args:
            item: 物品名称
            user_id: 用户ID

        Returns:
            包含查询结果的字典
        """
        normalized = normalize_item_name(item)
        now = get_timestamp()

        print(f"[数据库] 🔍 查询物品: {item}")
        print(f"[数据库]   规范化名称: {normalized}")

        cursor = self.conn.cursor()

        # 级别1: 精确匹配
        cursor.execute("""
            SELECT * FROM items
            WHERE user_id = ? AND normalized_name = ? AND is_deleted = 0
        """, (user_id, normalized))

        result = cursor.fetchone()
        if result:
            result_dict = dict(result)
            print(f"[数据库] ✓ 精确匹配成功, ID: {result_dict['id']}")

            # 更新访问统计
            cursor.execute("""
                UPDATE items
                SET query_count = query_count + 1,
                    last_accessed_at = ?
                WHERE id = ?
            """, (now, result_dict['id']))
            self.conn.commit()

            return {
                'status': 'success',
                'match_type': 'exact',
                'item': result_dict['item_name'],
                'location': result_dict['location'],
                'location_detail': result_dict['location_detail'],
                'moved_at': result_dict['moved_at'],
                'move_count': result_dict['move_count'],
                'message': f"{result_dict['item_name']}在{result_dict['location']}"
            }

        # 级别2: 别名匹配 (JSON 解析 + 逐一比对) + 验证
        print(f"[数据库] 精确匹配失败,尝试别名匹配...")

        # 获取所有未删除的物品
        cursor.execute("""
            SELECT * FROM items
            WHERE user_id = ? AND is_deleted = 0
        """, (user_id,))

        all_items = cursor.fetchall()
        matched_items = []

        # 逐一检查别名
        for row in all_items:
            item_dict = dict(row)

            # 解析 JSON 别名
            if item_dict.get('item_aliases'):
                try:
                    aliases = json.loads(item_dict['item_aliases'])

                    # 检查查询词是否在任何别名中
                    for alias in aliases:
                        alias_normalized = normalize_item_name(alias)
                        # 双向匹配: normalized 在 alias 中，或 alias 在 normalized 中
                        if normalized in alias_normalized or alias_normalized in normalized:
                            matched_items.append(item_dict)
                            print(f"[数据库]   别名匹配候选: {item_dict['item_name']} (别名: {alias})")
                            break
                except json.JSONDecodeError:
                    continue

        # 验证匹配结果
        if matched_items:
            for match in matched_items:
                if self._verify_item_name(match, item):
                    print(f"[数据库] ✓ 别名匹配成功(已验证): {match['item_name']}")

                    # 更新访问统计
                    cursor.execute("""
                        UPDATE items
                        SET query_count = query_count + 1,
                            last_accessed_at = ?
                        WHERE id = ?
                    """, (now, match['id']))
                    self.conn.commit()

                    return {
                        'status': 'success',
                        'match_type': 'alias',
                        'item': match['item_name'],
                        'location': match['location'],
                        'location_detail': match['location_detail'],
                        'message': f"找到相似物品: {match['item_name']}在{match['location']}"
                    }

            print(f"[数据库] 别名匹配验证失败,无匹配物品")

        # 级别3: FTS5 全文搜索 (带验证)
        print(f"[数据库] 别名匹配失败,尝试全文搜索...")
        try:
            cursor.execute("""
                SELECT items.* FROM items_fts
                JOIN items ON items_fts.rowid = items.id
                WHERE items_fts MATCH ?
                AND items.user_id = ?
                AND items.is_deleted = 0
                ORDER BY rank
                LIMIT 3
            """, (normalized, user_id))

            results = cursor.fetchall()
            if results:
                # 验证每个全文搜索结果
                for row in results:
                    match = dict(row)
                    if self._verify_item_name(match, item):
                        print(f"[数据库] ✓ 全文搜索成功(已验证): {match['item_name']}")

                        # 更新访问统计
                        cursor.execute("""
                            UPDATE items
                            SET query_count = query_count + 1,
                                last_accessed_at = ?
                            WHERE id = ?
                        """, (now, match['id']))
                        self.conn.commit()

                        return {
                            'status': 'success',
                            'match_type': 'fuzzy',
                            'item': match['item_name'],
                            'location': match['location'],
                            'location_detail': match['location_detail'],
                            'message': f"可能是: {match['item_name']}在{match['location']}"
                        }

                print(f"[数据库] 全文搜索验证失败,无匹配物品")
        except Exception as e:
            print(f"[数据库] 全文搜索失败: {e}")

        # 级别4: LIKE 中文模糊匹配 (关键词子串)
        print(f"[数据库] 全文搜索失败,尝试关键词模糊匹配...")
        keywords = extract_keywords(item)
        print(f"[数据库]   提取关键词: {keywords[:5]}")  # 只显示前5个

        for keyword in keywords:
            if len(keyword) < 2:  # 跳过太短的关键词
                continue

            cursor.execute("""
                SELECT * FROM items
                WHERE user_id = ?
                AND is_deleted = 0
                AND (item_name LIKE ? OR normalized_name LIKE ?)
                LIMIT 5
            """, (user_id, f'%{keyword}%', f'%{keyword}%'))

            results = cursor.fetchall()
            if results:
                # 验证每个匹配结果 - 使用 _verify_item_name
                for row in results:
                    match = dict(row)

                    # 必须通过名称验证
                    if self._verify_item_name(match, item):
                        # 计算匹配度: 匹配的关键词数量
                        match_score = sum(1 for kw in keywords if kw in match['normalized_name'])

                        print(f"[数据库] ✓ 关键词模糊匹配成功 (关键词: '{keyword}', 匹配度: {match_score}): {match['item_name']}")

                        # 更新访问统计
                        cursor.execute("""
                            UPDATE items
                            SET query_count = query_count + 1,
                                last_accessed_at = ?
                            WHERE id = ?
                        """, (now, match['id']))
                        self.conn.commit()

                        return {
                            'status': 'success',
                            'match_type': 'keyword_fuzzy',
                            'item': match['item_name'],
                            'location': match['location'],
                            'location_detail': match['location_detail'],
                            'match_keyword': keyword,
                            'match_score': match_score,
                            'message': f"找到相关物品: {match['item_name']}在{match['location']}"
                        }

        print(f"[数据库] 关键词模糊匹配失败,无匹配物品")

        # 未找到
        print(f"[数据库] ✗ 未找到物品: {item}")
        return {
            'status': 'not_found',
            'item': item,
            'message': f"没有找到{item}的位置记录"
        }

    def list_all_items(self, user_id: str = 'default',
                       include_deleted: bool = False) -> Dict[str, Any]:
        """
        列出所有物品

        Args:
            user_id: 用户ID
            include_deleted: 是否包含已删除的物品

        Returns:
            包含物品列表的字典
        """
        cursor = self.conn.cursor()

        query = """
            SELECT * FROM items
            WHERE user_id = ?
        """
        if not include_deleted:
            query += " AND is_deleted = 0"
        query += " ORDER BY updated_at DESC"

        cursor.execute(query, (user_id,))
        results = cursor.fetchall()

        items = []
        for row in results:
            row_dict = dict(row)
            items.append({
                'item': row_dict['item_name'],
                'location': row_dict['location'],
                'location_detail': row_dict['location_detail'],
                'created_at': row_dict['created_at'],
                'updated_at': row_dict['updated_at'],
                'moved_at': row_dict['moved_at'],
                'move_count': row_dict['move_count'],
                'query_count': row_dict['query_count']
            })

        print(f"[数据库] 列出所有物品: 共 {len(items)} 个")

        return {
            'status': 'success',
            'count': len(items),
            'items': items,
            'message': f"共找到 {len(items)} 个物品记录" if items else "还没有任何物品记录"
        }

    def get_item_history(self, item: str, user_id: str = 'default') -> Dict[str, Any]:
        """
        获取物品变更历史

        Args:
            item: 物品名称
            user_id: 用户ID

        Returns:
            包含历史记录的字典
        """
        normalized = normalize_item_name(item)
        cursor = self.conn.cursor()

        # 先找到物品ID
        cursor.execute("""
            SELECT id FROM items
            WHERE user_id = ? AND normalized_name = ?
        """, (user_id, normalized))

        result = cursor.fetchone()
        if not result:
            return {
                'status': 'not_found',
                'message': f"没有找到{item}的记录"
            }

        item_id = result['id']

        # 获取历史记录
        cursor.execute("""
            SELECT * FROM item_history
            WHERE item_id = ?
            ORDER BY timestamp DESC
        """, (item_id,))

        history = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            history.append({
                'action': row_dict['action'],
                'location': row_dict['location'],
                'old_value': row_dict['old_value'],
                'new_value': row_dict['new_value'],
                'timestamp': row_dict['timestamp']
            })

        return {
            'status': 'success',
            'count': len(history),
            'history': history
        }

    def delete_item(self, item: str, user_id: str = 'default',
                    soft: bool = True) -> Dict[str, Any]:
        """
        删除物品

        Args:
            item: 物品名称
            user_id: 用户ID
            soft: 是否软删除 (默认True)

        Returns:
            操作结果
        """
        normalized = normalize_item_name(item)
        cursor = self.conn.cursor()

        if soft:
            # 软删除
            cursor.execute("""
                UPDATE items
                SET is_deleted = 1, updated_at = ?
                WHERE user_id = ? AND normalized_name = ?
            """, (get_timestamp(), user_id, normalized))
        else:
            # 硬删除
            cursor.execute("""
                DELETE FROM items
                WHERE user_id = ? AND normalized_name = ?
            """, (user_id, normalized))

        self.conn.commit()

        if cursor.rowcount > 0:
            return {
                'status': 'success',
                'message': f"已删除{item}"
            }
        else:
            return {
                'status': 'not_found',
                'message': f"没有找到{item}"
            }

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("[数据库] 连接已关闭")


# 全局数据库实例 (延迟初始化)
_db_instance: Optional[ItemDatabase] = None
_db_lock = threading.Lock()  # 线程锁保护单例初始化


def get_database() -> ItemDatabase:
    """获取全局数据库实例 (线程安全单例模式)

    使用双重检查锁定 (Double-Checked Locking) 模式:
    - 第一次检查(无锁): 如果实例已存在,直接返回(快速路径)
    - 获取锁: 多个线程竞争锁,只有一个线程能获取
    - 第二次检查(有锁): 确保只有一个线程初始化实例
    """
    global _db_instance

    # 第一次检查 (无锁) - 快速路径
    if _db_instance is None:
        with _db_lock:  # 获取锁
            # 第二次检查 (有锁) - 确保只有一个线程初始化
            if _db_instance is None:
                from config import config
                db_path = config.DATA_DIR / "items.db"
                _db_instance = ItemDatabase(db_path)

    return _db_instance
