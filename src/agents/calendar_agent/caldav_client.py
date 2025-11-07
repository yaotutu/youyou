"""CalDAV 客户端管理器

管理与 CalDAV 服务器的连接和操作
"""
import caldav
from icalendar import Calendar as iCal, Event, Alarm
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

from config import config
from core.logger import logger


class CalDAVManager:
    """CalDAV 客户端管理器（单例）"""

    _instance: Optional['CalDAVManager'] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化 CalDAV 连接"""
        if self._initialized:
            return

        if not config.CALDAV_URL:
            raise ValueError(
                "未配置 CalDAV 服务器。请在 .env 中设置 CALDAV_URL、"
                "CALDAV_USERNAME 和 CALDAV_PASSWORD"
            )

        self.client = None
        self.calendar = None
        self._connect()
        self._initialized = True

    def _connect(self):
        """连接到 CalDAV 服务器"""
        logger.info("[CalDAV] 🔗 正在连接服务器...")

        try:
            # 创建 CalDAV 客户端
            self.client = caldav.DAVClient(
                url=config.CALDAV_URL,
                username=config.CALDAV_USERNAME,
                password=config.CALDAV_PASSWORD
            )

            # 获取 Principal（用户主体）
            principal = self.client.principal()

            # 获取日历列表
            calendars = principal.calendars()

            if not calendars:
                # 如果没有日历，创建一个
                logger.info("[CalDAV] 📅 未找到日历，正在创建...")
                calendar_name = config.CALDAV_CALENDAR_NAME or "YouYou 提醒"
                self.calendar = principal.make_calendar(name=calendar_name)
                logger.success(f"[CalDAV] ✅ 已创建日历：{calendar_name}")
            else:
                # 使用指定日历或第一个日历
                calendar_name = config.CALDAV_CALENDAR_NAME
                if calendar_name:
                    self.calendar = next(
                        (c for c in calendars if c.name == calendar_name),
                        calendars[0]
                    )
                else:
                    self.calendar = calendars[0]

                logger.success(f"[CalDAV] ✅ 已连接到日历：{self.calendar.name}")

        except Exception as e:
            raise ConnectionError(f"CalDAV 连接失败：{str(e)}")

    def add_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 30,
        reminder_minutes: int = 10,
        description: str = ""
    ) -> str:
        """
        添加日历事件

        Args:
            summary: 事件摘要
            start_time: 开始时间
            duration_minutes: 持续时间（分钟）
            reminder_minutes: 提前提醒时间（分钟）
            description: 事件描述

        Returns:
            事件 UID

        Raises:
            Exception: 添加失败时抛出异常
        """
        try:
            # 创建事件
            event = Event()
            event_uid = str(uuid.uuid4())

            event.add('uid', event_uid)
            event.add('summary', summary)
            event.add('dtstart', start_time)
            event.add('dtend', start_time + timedelta(minutes=duration_minutes))
            event.add('dtstamp', datetime.now())

            # 添加描述
            if description:
                event.add('description', description)

            # 添加提醒（VALARM）
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('DESCRIPTION', summary)
            alarm.add('TRIGGER', timedelta(minutes=-reminder_minutes))
            event.add_component(alarm)

            # 创建日历容器并添加事件
            cal = iCal()
            cal.add_component(event)

            # 保存到 CalDAV 服务器
            self.calendar.save_event(cal.to_ical())

            logger.success(f"[CalDAV] ✅ 事件已添加：{event_uid}")
            return event_uid

        except Exception as e:
            raise Exception(f"添加事件失败：{str(e)}")

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """
        获取即将到来的事件

        Args:
            days_ahead: 未来几天

        Returns:
            事件列表，每个事件包含 uid、summary、start_time、end_time
        """
        try:
            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)

            # 搜索事件
            events = self.calendar.date_search(
                start=now,
                end=end_date,
                expand=True
            )

            result = []
            for event in events:
                try:
                    ical_event = event.icalendar_component
                    dtstart = ical_event.get('dtstart')
                    dtend = ical_event.get('dtend')

                    result.append({
                        'uid': str(ical_event.get('uid', '')),
                        'summary': str(ical_event.get('summary', '无标题')),
                        'start_time': dtstart.dt.isoformat() if dtstart else '',
                        'end_time': dtend.dt.isoformat() if dtend else '',
                    })
                except Exception as e:
                    logger.warning(f"[CalDAV] ⚠️ 解析事件失败：{e}")
                    continue

            # 按开始时间排序
            result.sort(key=lambda x: x['start_time'])
            return result

        except Exception as e:
            raise Exception(f"查询事件失败：{str(e)}")

    def delete_event(self, event_uid: str):
        """
        删除事件

        Args:
            event_uid: 事件 UID

        Raises:
            ValueError: 未找到事件时抛出
        """
        try:
            # 搜索所有事件
            events = self.calendar.events()

            for event in events:
                ical = event.icalendar_component
                if str(ical.get('uid', '')) == event_uid:
                    event.delete()
                    logger.success(f"[CalDAV] ✅ 已删除事件：{event_uid}")
                    return

            raise ValueError(f"未找到事件：{event_uid}")

        except Exception as e:
            raise Exception(f"删除事件失败：{str(e)}")

    def close(self):
        """关闭连接"""
        if self.client:
            try:
                self.client.close()
                logger.info("[CalDAV] 🔌 连接已关闭")
            except Exception:
                pass

    def __del__(self):
        """清理连接"""
        self.close()
