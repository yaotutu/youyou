"""会话历史管理器

提供内存级别的会话历史缓存,减少对 Zep 的远程调用:
- 首次访问从 Zep 加载历史
- 后续请求使用内存缓存
- 支持定期刷新策略
- 异步写入 Zep 持久化
"""
import threading
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.zep_memory import get_zep_memory
from core.logger import logger


class SessionHistoryManager:
    """会话历史管理器

    设计理念:
    - 读: 首次从 Zep 加载,后续用内存
    - 写: 立即写内存 + 异步写 Zep
    - 定期刷新: 可选的定期从 Zep 重新加载
    """

    def __init__(self, max_history_length: int = 10, refresh_interval: int = 300):
        """初始化会话历史管理器

        Args:
            max_history_length: 保留的最大历史消息轮数 (user+assistant算1轮)
            refresh_interval: 刷新间隔(秒),0表示不自动刷新
        """
        self._histories: Dict[str, List[Dict[str, Any]]] = {}  # {user_id: [messages]}
        self._last_refresh: Dict[str, float] = {}  # {user_id: timestamp}
        self._max_length = max_history_length
        self._refresh_interval = refresh_interval
        self._lock = threading.RLock()

        logger.info(f"[会话历史] 初始化管理器: 最大历史={max_history_length}轮, 刷新间隔={refresh_interval}秒")

    def get_history(self, user_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """获取用户的会话历史

        Args:
            user_id: 用户ID
            force_refresh: 是否强制从 Zep 刷新

        Returns:
            消息列表 [{"role": "user/assistant", "content": "..."}]
        """
        with self._lock:
            now = time.time()

            # 判断是否需要从 Zep 加载/刷新
            should_load = (
                force_refresh or
                user_id not in self._histories or
                (self._refresh_interval > 0 and
                 user_id in self._last_refresh and
                 now - self._last_refresh[user_id] > self._refresh_interval)
            )

            if should_load:
                try:
                    logger.info(f"[会话历史] 从 Zep 加载历史: user_id={user_id}")
                    zep = get_zep_memory()
                    messages = zep.get_recent_context(limit=self._max_length * 2)

                    # 转换格式
                    self._histories[user_id] = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in messages
                    ]
                    self._last_refresh[user_id] = now

                    logger.success(f"[会话历史] ✓ 加载了 {len(self._histories[user_id])} 条消息")
                except Exception as e:
                    logger.warning(f"[会话历史] ⚠️  从 Zep 加载失败: {e}")
                    # 如果加载失败但已有缓存,继续使用缓存
                    if user_id not in self._histories:
                        self._histories[user_id] = []

            return self._histories.get(user_id, []).copy()  # 返回副本,避免外部修改

    def add_interaction(self, user_id: str, user_input: str, assistant_response: str,
                       agent_name: Optional[str] = None,
                       async_persist: bool = True) -> None:
        """添加一轮交互到会话历史

        Args:
            user_id: 用户ID
            user_input: 用户输入
            assistant_response: 助手响应
            agent_name: 处理该请求的 Agent 名称
            async_persist: 是否异步持久化到 Zep
        """
        with self._lock:
            # 确保历史存在
            if user_id not in self._histories:
                self._histories[user_id] = []

            # 添加到内存历史
            self._histories[user_id].append({"role": "user", "content": user_input})
            self._histories[user_id].append({"role": "assistant", "content": assistant_response})

            # 保持最大长度限制 (在添加之后立即裁剪)
            max_messages = self._max_length * 2  # user + assistant (一轮 = 2条)
            if len(self._histories[user_id]) > max_messages:
                # 保留最新的 max_messages 条
                removed = len(self._histories[user_id]) - max_messages
                self._histories[user_id] = self._histories[user_id][-max_messages:]
                logger.info(f"[会话历史]   裁剪历史: 移除 {removed} 条旧消息, 保留最新 {max_messages} 条")

            logger.success(f"[会话历史] ✓ 添加到内存: {user_input[:30]}... (当前 {len(self._histories[user_id])} 条)")

        # 异步持久化到 Zep
        if async_persist:
            def _persist():
                try:
                    zep = get_zep_memory()
                    zep.add_interaction(
                        user_input=user_input,
                        assistant_response=assistant_response,
                        agent_name=agent_name,
                        metadata={"timestamp": datetime.now().isoformat()}
                    )
                except Exception as e:
                    logger.warning(f"[会话历史] ⚠️  异步持久化到 Zep 失败: {e}")

            thread = threading.Thread(target=_persist, daemon=True)
            thread.start()

    def clear_history(self, user_id: str) -> None:
        """清除用户的会话历史 (仅内存,不影响 Zep)

        Args:
            user_id: 用户ID
        """
        with self._lock:
            if user_id in self._histories:
                del self._histories[user_id]
                logger.success(f"[会话历史] ✓ 清除内存历史: user_id={user_id}")

            if user_id in self._last_refresh:
                del self._last_refresh[user_id]

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户的会话统计信息

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        with self._lock:
            history = self._histories.get(user_id, [])
            last_refresh = self._last_refresh.get(user_id, 0)

            return {
                "user_id": user_id,
                "message_count": len(history),
                "last_refresh": datetime.fromtimestamp(last_refresh).isoformat() if last_refresh else None,
                "cache_age_seconds": int(time.time() - last_refresh) if last_refresh else None
            }


# 全局单例
_session_manager: Optional[SessionHistoryManager] = None
_manager_lock = threading.Lock()


def get_session_manager(max_history_length: int = 10,
                        refresh_interval: int = 300) -> SessionHistoryManager:
    """获取全局会话历史管理器实例 (线程安全单例)

    Args:
        max_history_length: 保留的最大历史消息轮数
        refresh_interval: 刷新间隔(秒),0表示不自动刷新

    Returns:
        SessionHistoryManager 实例
    """
    global _session_manager

    if _session_manager is None:
        with _manager_lock:
            if _session_manager is None:
                _session_manager = SessionHistoryManager(
                    max_history_length=max_history_length,
                    refresh_interval=refresh_interval
                )

    return _session_manager
