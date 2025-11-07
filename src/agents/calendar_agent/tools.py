"""CalendarAgent 工具函数"""
from langchain_core.tools import tool
from typing import Optional
from datetime import datetime

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
) -> str:
    """
    添加日历提醒

    Args:
        user_input: 用户的自然语言输入（如："明天上午八点提醒我拿充电器"）
        custom_reminder_minutes: 自定义提前提醒时间（分钟），不提供则使用默认值

    Returns:
        添加结果消息
    """
    try:
        # 1. 使用 LLM 解析时间
        print(f"[calendar_agent] 📝 解析用户输入: {user_input}")
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

        return f"""✅ 提醒已添加！

📅 **时间**：{reminder.start_time.strftime('%Y-%m-%d %H:%M')}
📝 **内容**：{reminder.summary}
⏰ **提前提醒**：{reminder.reminder_minutes} 分钟
⏱️ **持续时间**：{reminder.duration_minutes} 分钟
🔖 **事件ID**：{event_uid}"""

    except ValueError as e:
        return f"❌ 时间解析失败：{str(e)}\n\n请提供更明确的时间信息，例如：\n- 明天上午8点\n- 下周五下午3点\n- 后天中午12点"
    except Exception as e:
        error_msg = str(e)
        if "CalDAV" in error_msg or "连接" in error_msg:
            return f"❌ CalDAV 连接失败：{error_msg}\n\n请检查 .env 文件中的配置：\n- CALDAV_URL\n- CALDAV_USERNAME\n- CALDAV_PASSWORD"
        return f"❌ 添加提醒失败：{error_msg}"


@tool
def list_upcoming_reminders(days_ahead: int = 7) -> str:
    """
    列出即将到来的提醒

    Args:
        days_ahead: 查询未来几天的提醒（默认7天）

    Returns:
        提醒列表
    """
    try:
        manager = _get_caldav_manager()
        events = manager.get_upcoming_events(days_ahead)

        if not events:
            return f"📭 未来 {days_ahead} 天内没有提醒"

        # 按日期分组
        events_by_date = {}
        for event in events:
            try:
                start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                date_key = start_time.strftime('%Y-%m-%d')
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append({
                    **event,
                    'start_dt': start_time
                })
            except Exception:
                continue

        # 构建响应
        result = f"📅 **未来 {days_ahead} 天的提醒**（共 {len(events)} 条）\n\n"

        for date_key in sorted(events_by_date.keys()):
            date_events = events_by_date[date_key]
            date_obj = datetime.fromisoformat(date_key)
            date_display = date_obj.strftime('%Y-%m-%d (%A)')

            result += f"### {date_display}\n\n"

            for i, event in enumerate(date_events, 1):
                time_display = event['start_dt'].strftime('%H:%M')
                result += f"{i}. **{event['summary']}**\n"
                result += f"   - 时间：{time_display}\n"
                result += f"   - ID：`{event['uid']}`\n\n"

        return result

    except Exception as e:
        error_msg = str(e)
        if "CalDAV" in error_msg or "连接" in error_msg:
            return f"❌ CalDAV 连接失败：{error_msg}\n\n请检查 .env 文件中的配置。"
        return f"❌ 查询提醒失败：{error_msg}"


@tool
def delete_calendar_reminder(event_uid: str) -> str:
    """
    删除日历提醒

    Args:
        event_uid: 事件ID（从 list_upcoming_reminders 获取）

    Returns:
        删除结果
    """
    try:
        manager = _get_caldav_manager()
        manager.delete_event(event_uid)
        return f"✅ 已删除提醒（ID：{event_uid}）"

    except ValueError as e:
        return f"❌ 未找到提醒：{str(e)}\n\n请先使用'列出提醒'获取正确的事件ID。"
    except Exception as e:
        error_msg = str(e)
        if "CalDAV" in error_msg or "连接" in error_msg:
            return f"❌ CalDAV 连接失败：{error_msg}\n\n请检查 .env 文件中的配置。"
        return f"❌ 删除失败：{error_msg}"


def get_calendar_tools():
    """获取 CalendarAgent 的所有工具"""
    return [
        add_calendar_reminder,
        list_upcoming_reminders,
        delete_calendar_reminder
    ]
