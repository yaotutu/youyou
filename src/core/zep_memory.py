"""Zep 全局记忆管理器 (基于 Zep 3.0 API)

作为系统的最顶层记忆中枢:
- 记录所有用户输入和 Agent 响应
- 提供语义搜索能力
- 作为其他记忆系统的兜底方案
"""
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import config
from core.logger import logger


class ZepMemoryManager:
    """Zep 全局记忆管理器 (Zep 3.0)

    设计理念:
    - 记录所有对话,无论是否被结构化存储
    - 提供语义搜索,补充精确查询的不足
    - 支持上下文理解和意图推理
    """

    def __init__(self):
        """初始化 Zep 客户端"""
        self._client = None
        self._lock = threading.RLock()
        self._initialized = False
        self._use_cloud = False

    def _ensure_initialized(self):
        """延迟初始化 Zep 客户端"""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            logger.info("\n[Zep记忆] 🚀 初始化全局记忆中枢 (Zep 3.0)...")

            try:
                # 判断使用 Cloud 还是本地部署
                if hasattr(config, 'ZEP_API_KEY') and config.ZEP_API_KEY:
                    # Zep Cloud 3.0
                    from zep_cloud import Zep
                    self._client = Zep(api_key=config.ZEP_API_KEY)
                    self._use_cloud = True
                    logger.success("[Zep记忆] ✓ 使用 Zep Cloud 3.0")
                else:
                    # 本地部署 (使用 zep-python SDK)
                    from zep_python import ZepClient
                    zep_url = getattr(config, 'ZEP_API_URL', 'http://localhost:8000')
                    self._client = ZepClient(base_url=zep_url)
                    self._use_cloud = False
                    logger.success(f"[Zep记忆] ✓ 使用本地 Zep: {zep_url}")

                # 确保 user 和 thread 存在
                self._ensure_user_and_thread()

                self._initialized = True
                logger.success("[Zep记忆] ✓ 初始化完成\n")

            except Exception as e:
                logger.error(f"[Zep记忆] ✗ 初始化失败: {e}")
                logger.warning("[Zep记忆] ⚠️  将在无记忆模式下运行")
                import traceback
                traceback.print_exc()
                self._client = None

    def _ensure_user_and_thread(self):
        """确保 user 和 thread 存在 (Zep 3.0)"""
        if not self._client:
            return

        try:
            if self._use_cloud:
                # Zep Cloud 3.0 - 创建 user 和 thread
                # 1. 创建或获取 user
                try:
                    self._client.user.get(user_id=config.USER_ID)
                    logger.success(f"[Zep记忆] ✓ User 已存在: {config.USER_ID}")
                except Exception:
                    # User 不存在，创建新 user
                    self._client.user.add(
                        user_id=config.USER_ID,
                        email=f"{config.USER_ID}@youyou.local",
                        metadata={"app": "youyou", "created_at": datetime.now().isoformat()}
                    )
                    logger.success(f"[Zep记忆] ✓ 创建新 user: {config.USER_ID}")

                # 2. 创建或获取 thread
                try:
                    self._client.thread.get(thread_id=config.USER_ID)
                    logger.success(f"[Zep记忆] ✓ Thread 已存在: {config.USER_ID}")
                except Exception:
                    # Thread 不存在，创建新 thread
                    # Zep 3.0 API: 只需要 thread_id 和 user_id
                    self._client.thread.create(
                        thread_id=config.USER_ID,
                        user_id=config.USER_ID
                    )
                    logger.success(f"[Zep记忆] ✓ 创建新 thread: {config.USER_ID}")
            else:
                # 本地 Zep - 使用 memory/session API
                try:
                    self._client.memory.get_session(config.USER_ID)
                except Exception:
                    # Session 不存在，创建新 session
                    from zep_python.memory import Session
                    self._client.memory.add_session(
                        Session(
                            session_id=config.USER_ID,
                            user_id=config.USER_ID,
                            metadata={
                                "created_at": datetime.now().isoformat(),
                                "app": "youyou"
                            }
                        )
                    )
                    logger.success(f"[Zep记忆] ✓ 创建新 session: {config.USER_ID}")
        except Exception as e:
            logger.warning(f"[Zep记忆] ⚠️  创建 user/thread 时出错: {e}")

    def add_message(self, role: str, content: str,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加消息到 Zep (Zep 3.0)

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 额外元数据

        Returns:
            是否成功
        """
        self._ensure_initialized()

        if not self._client:
            return False

        try:
            meta = metadata or {}
            meta['timestamp'] = datetime.now().isoformat()

            if self._use_cloud:
                # Zep Cloud 3.0 - 使用 Message 对象
                from zep_cloud import Message
                self._client.thread.add_messages(
                    thread_id=config.USER_ID,
                    messages=[
                        Message(
                            role=role,
                            content=content,
                            metadata=meta
                        )
                    ]
                )
            else:
                # 本地 Zep
                from zep_python.memory import Message
                self._client.memory.add_memory(
                    session_id=config.USER_ID,
                    messages=[
                        Message(
                            role=role,
                            content=content,
                            metadata=meta
                        )
                    ]
                )

            logger.success(f"[Zep记忆] ✓ 记录消息 ({role}): {content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 添加消息失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_interaction(self, user_input: str, assistant_response: str,
                       agent_name: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """记录完整的交互(用户输入 + 助手响应) (Zep 3.0)

        Args:
            user_input: 用户输入
            assistant_response: 助手响应
            agent_name: 处理该请求的 Agent 名称
            metadata: 额外元数据

        Returns:
            是否成功
        """
        self._ensure_initialized()

        if not self._client:
            return False

        try:
            meta = metadata or {}
            if agent_name:
                meta['agent'] = agent_name
            meta['timestamp'] = datetime.now().isoformat()

            if self._use_cloud:
                # Zep Cloud 3.0 - 一次性添加多条消息
                from zep_cloud import Message
                self._client.thread.add_messages(
                    thread_id=config.USER_ID,
                    messages=[
                        Message(role="user", content=user_input, metadata=meta),
                        Message(role="assistant", content=assistant_response, metadata=meta)
                    ]
                )
            else:
                # 本地 Zep
                from zep_python.memory import Message
                self._client.memory.add_memory(
                    session_id=config.USER_ID,
                    messages=[
                        Message(role="user", content=user_input, metadata=meta),
                        Message(role="assistant", content=assistant_response, metadata=meta)
                    ]
                )

            logger.success(f"[Zep记忆] ✓ 记录交互: {user_input[:30]}... -> {assistant_response[:30]}...")
            return True

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 记录交互失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """语义搜索历史记忆 (Zep 3.0)

        注意: Zep 3.0 的搜索功能可能在 Graph API 中，这里提供基础实现

        Args:
            query: 搜索查询 (语义化描述)
            limit: 返回结果数量

        Returns:
            匹配的记忆列表
        """
        self._ensure_initialized()

        if not self._client:
            return []

        try:
            logger.debug(f"[Zep记忆] 🔍 语义搜索: {query}")

            # Zep 3.0: 搜索功能可能需要使用 Graph API
            # 这里我们简单地获取最近的消息并在客户端进行过滤
            # 更好的方案是使用 Zep 的 Graph API 进行语义搜索

            messages = self.get_recent_context(limit=50)  # 获取更多消息用于搜索

            # 改进的关键词匹配: 拆分查询为多个关键词
            # 移除常见的停用词
            stopwords = {'的', '了', '在', '是', '和', '与', '或', '等', '着', '呢', '吗', '吧', '啊'}

            # 按空格分词，同时也尝试按停用词分词
            raw_words = query.split()
            query_keywords = []

            for word in raw_words:
                # 移除停用词
                for stopword in stopwords:
                    word = word.replace(stopword, ' ')
                # 分割后的词
                sub_words = [w.strip() for w in word.split() if w.strip()]
                query_keywords.extend(sub_words)

            # 去重并保持顺序
            seen = set()
            query_keywords = [w for w in query_keywords if not (w in seen or seen.add(w))]

            # 如果没有有效关键词，尝试直接匹配
            if not query_keywords:
                query_keywords = [query]

            logger.debug(f"[Zep记忆]   搜索关键词: {query_keywords}")

            # 计算每条消息的匹配分数
            scored_messages = []
            for msg in messages:
                content_lower = msg['content'].lower()
                score = 0

                # 统计匹配的关键词数量
                for keyword in query_keywords:
                    if keyword.lower() in content_lower:
                        score += 1

                # 至少匹配一个关键词才加入结果
                if score > 0:
                    scored_messages.append({
                        'role': msg['role'],
                        'content': msg['content'],
                        'score': score / len(query_keywords),  # 归一化分数
                        'metadata': msg.get('metadata', {})
                    })

            # 按分数排序，取前 N 个
            scored_messages.sort(key=lambda x: x['score'], reverse=True)
            memories = scored_messages[:limit]

            logger.success(f"[Zep记忆] ✓ 找到 {len(memories)} 条相关记忆")
            return memories

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话上下文 (Zep 3.0)

        Args:
            limit: 获取消息数量

        Returns:
            最近的消息列表
        """
        self._ensure_initialized()

        if not self._client:
            return []

        try:
            if self._use_cloud:
                # Zep Cloud 3.0 - 使用 thread.get() 获取消息
                thread = self._client.thread.get(thread_id=config.USER_ID)
                source = thread
            else:
                # 本地 Zep
                session = self._client.memory.get_session(config.USER_ID)
                source = session

            if not source or not hasattr(source, 'messages'):
                return []

            messages = []
            for msg in source.messages[-limit:]:
                messages.append({
                    'role': msg.role,
                    'content': msg.content,
                    'metadata': getattr(msg, 'metadata', {})
                })

            logger.success(f"[Zep记忆] ✓ 获取最近 {len(messages)} 条上下文")
            return messages

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 获取上下文失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_session_summary(self) -> Optional[str]:
        """获取会话摘要 (Zep 自动生成) (Zep 3.0)

        Returns:
            会话摘要文本
        """
        self._ensure_initialized()

        if not self._client:
            return None

        try:
            if self._use_cloud:
                thread = self._client.thread.get(thread_id=config.USER_ID)
                source = thread
            else:
                session = self._client.memory.get_session(config.USER_ID)
                source = session

            if source and hasattr(source, 'summary') and source.summary:
                summary = source.summary
                logger.success(f"[Zep记忆] ✓ 获取会话摘要: {summary[:100]}...")
                return summary

            return None

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 获取摘要失败: {e}")
            return None

    def extract_facts(self) -> List[str]:
        """提取 Zep 自动识别的事实 (Zep 3.0)

        Returns:
            事实列表
        """
        self._ensure_initialized()

        if not self._client:
            return []

        try:
            if self._use_cloud:
                thread = self._client.thread.get(thread_id=config.USER_ID)
                source = thread
            else:
                session = self._client.memory.get_session(config.USER_ID)
                source = session

            if source and hasattr(source, 'facts') and source.facts:
                facts = [fact.fact if hasattr(fact, 'fact') else str(fact) for fact in source.facts]
                logger.success(f"[Zep记忆] ✓ 提取到 {len(facts)} 条事实")
                return facts

            return []

        except Exception as e:
            logger.error(f"[Zep记忆] ✗ 提取事实失败: {e}")
            return []


# 全局单例 (延迟初始化)
_zep_instance: Optional[ZepMemoryManager] = None
_zep_lock = threading.Lock()


def get_zep_memory() -> ZepMemoryManager:
    """获取全局 Zep 记忆管理器实例 (线程安全单例)

    Returns:
        ZepMemoryManager 实例
    """
    global _zep_instance

    # 双重检查锁定
    if _zep_instance is None:
        with _zep_lock:
            if _zep_instance is None:
                _zep_instance = ZepMemoryManager()

    return _zep_instance
