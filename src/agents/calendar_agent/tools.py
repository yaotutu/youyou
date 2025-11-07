"""CalendarAgent 工具函数"""
from langchain_core.tools import tool
from typing import Optional
from datetime import datetime

from core.logger import logger
from .time_parser import parse_time_from_natural_language
from .caldav_client import CalDAVManager
from config import config


# 全局 CalDAV 管理器（单例）
_caldav_manager: Optional[CalDAVManager] = None


def _get_caldav_manager() -> CalDAVManager:
    """获取 CalDAV 管理器实例（单例）"""
    global _caldav_manager
    if _caldav_manager is None:
        try:
            _caldav_manager = CalDAVManager()
        except Exception as e:
            raise Exception(
                f"初始化 CalDAV 管理器失败：{str(e)}\n"
                "请检查 .env 文件中的 CalDAV 配置。"
            )
    return _caldav_manager


@tool
def add_calendar_reminder(
    user_input: str,
    custom_reminder_minutes: Optional[int] = None
) -> dict:
    """
    添加日历提醒

    Args:
        user_input: 用户的自然语言输入（如："明天上午八点提醒我拿充电器"）
        custom_reminder_minutes: 自定义提前提醒时间（分钟），不提供则使用默认值

    Returns:
        包含 action_type 和 data 的字典
    """
    try:
        # 1. 使用 LLM 解析时间
        logger.info(f"[calendar_agent] 📝 解析用户输入: {user_input}")
        reminder = parse_time_from_natural_language(user_input)

        # 2. 覆盖提醒时间（如果指定）
        if custom_reminder_minutes is not None:
            reminder.reminder_minutes = custom_reminder_minutes

        # 3. 创建日历事件
        manager = _get_caldav_manager()
        event_uid = manager.add_event(
            summary=reminder.summary,
            start_time=reminder.start_time,
            duration_minutes=reminder.duration_minutes,
            reminder_minutes=reminder.reminder_minutes,
            description=f"由 YouYou 创建于 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # 返回结构化数据
        formatted_time = reminder.start_time.strftime('%Y-%m-%d %H:%M')

        return {
            "action_type": "reminder_set",
            "data": {
                "title": reminder.summary,
                "time": formatted_time,
                "reminder_minutes": reminder.reminder_minutes,
                "duration_minutes": reminder.duration_minutes,
                "reminder_id": event_uid
            },
            "message": f"✅ 提醒已添加：{reminder.summary}（{formatted_time}）"
        }

    except ValueError as e:
        return {
            "action_type": "error",
            "data": {"error": str(e)},
            "message": f"❌ 时间解析失败：{str(e)}"
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "action_type": "error",
            "data": {"error": error_msg},
            "message": f"❌ 添加提醒失败：{error_msg}"
        }


@tool
def list_upcoming_reminders(days_ahead: int = 7) -> dict:
    """
    列出即将到来的提醒

    Args:
        days_ahead: 查询未来几天的提醒（默认7天）

    Returns:
        包含 action_type 和 data 的字典
    """
    try:
        manager = _get_caldav_manager()
        events = manager.get_upcoming_events(days_ahead)

        if not events:
            return {
                "action_type": "reminder_list",
                "data": {
                    "reminders": [],
                    "count": 0,
                    "days_ahead": days_ahead
                },
                "message": f"📭 未来 {days_ahead} 天内没有提醒"
            }

        # 整理事件数据
        reminders = []
        for event in events:
            try:
                start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                reminders.append({
                    "title": event['summary'],
                    "time": start_time.strftime('%Y-%m-%d %H:%M'),
                    "reminder_id": event['uid'],
                    "date": start_time.strftime('%Y-%m-%d')
                })
            except Exception:
                continue

        # 构建人类可读消息
        message = f"📅 未来 {days_ahead} 天的提醒（共 {len(reminders)} 条）"

        return {
            "action_type": "reminder_list",
            "data": {
                "reminders": reminders,
                "count": len(reminders),
                "days_ahead": days_ahead
            },
            "message": message
        }

    except Exception as e:
        error_msg = str(e)
        return {
            "action_type": "error",
            "data": {"error": error_msg},
            "message": f"❌ 查询提醒失败：{error_msg}"
        }


@tool
def delete_calendar_reminder(event_uid: str) -> dict:
    """
    删除日历提醒

    Args:
        event_uid: 事件ID（从 list_upcoming_reminders 获取）

    Returns:
        包含 action_type 和 data 的字典
    """
    try:
        manager = _get_caldav_manager()
        manager.delete_event(event_uid)

        return {
            "action_type": "reminder_deleted",
            "data": {
                "reminder_id": event_uid
            },
            "message": f"✅ 已删除提醒（ID：{event_uid}）"
        }

    except ValueError as e:
        return {
            "action_type": "error",
            "data": {"error": str(e)},
            "message": f"❌ 未找到提醒：{str(e)}"
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "action_type": "error",
            "data": {"error": error_msg},
            "message": f"❌ 删除失败：{error_msg}"
        }


def get_calendar_tools():
    """获取 CalendarAgent 的所有工具"""
    return [
        add_calendar_reminder,
        list_upcoming_reminders,
        delete_calendar_reminder
    ]
