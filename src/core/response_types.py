"""响应类型系统 - 支持结构化 API 响应

定义了统一的响应格式，支持从 Agent 到客户端的端到端结构化数据流。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import json


# 定义所有支持的操作类型
ActionType = Literal[
    # CalendarAgent
    "reminder_set",         # 提醒已设置
    "reminder_list",        # 提醒列表
    "reminder_deleted",     # 提醒已删除
    # NoteAgent
    "note_saved",           # 笔记已保存
    "note_search_results",  # 笔记搜索结果
    # ItemAgent
    "item_remembered",      # 物品位置已记录
    "item_location",        # 物品位置查询结果
    "item_list",            # 物品列表
    # ChatAgent
    "chat_response",        # 普通对话
    # 通用
    "error",                # 错误
]


@dataclass
class Action:
    """单个操作的结构

    Attributes:
        type: 操作类型
        data: 操作相关的结构化数据
    """
    type: ActionType
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type,
            "data": self.data
        }


@dataclass
class AgentResponse:
    """Agent 统一响应格式

    这是所有 Agent 返回的标准结构，支持：
    - 成功/失败状态
    - 人类可读消息
    - 结构化操作数据（支持多操作）
    - 时间戳

    Attributes:
        success: 操作是否成功
        agent: 处理此请求的 Agent 名称
        message: 人类可读的消息文本
        actions: 操作列表（一次请求可能触发多个操作）
        timestamp: 响应时间戳
        error: 错误信息（仅当 success=False 时）
    """
    success: bool
    agent: str
    message: str
    actions: List[Action] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 响应）

        Returns:
            包含所有非 None 字段的字典
        """
        result = {
            "success": self.success,
            "agent": self.agent,
            "message": self.message,
            "timestamp": self.timestamp,
            "actions": [action.to_dict() for action in self.actions]
        }

        # 只在失败时添加 error 字段
        if self.error:
            result["error"] = self.error

        return result

    def to_json(self) -> str:
        """转换为 JSON 字符串

        Returns:
            格式化的 JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def error_response(cls, agent: str, error: str) -> "AgentResponse":
        """创建错误响应的便捷方法

        Args:
            agent: Agent 名称
            error: 错误消息

        Returns:
            标记为失败的 AgentResponse 对象
        """
        return cls(
            success=False,
            agent=agent,
            message=f"错误：{error}",
            error=error,
            actions=[]
        )


__all__ = [
    "ActionType",
    "Action",
    "AgentResponse",
]
