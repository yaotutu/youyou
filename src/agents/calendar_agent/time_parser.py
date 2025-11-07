"""时间解析模块

使用 LLM 从自然语言中提取时间信息
"""
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import config


class CalendarReminder(BaseModel):
    """日历提醒模型"""

    summary: str = Field(description="提醒内容（简洁明了）")
    datetime_iso: str = Field(
        description="提醒时间（ISO 8601格式：YYYY-MM-DDTHH:MM:SS）"
    )
    reminder_minutes: int = Field(
        default=10,
        description="提前提醒时间（分钟，默认10分钟）"
    )
    duration_minutes: int = Field(
        default=30,
        description="事件持续时间（分钟，默认30分钟）"
    )

    @property
    def start_time(self) -> datetime:
        """将 ISO 字符串转换为 datetime 对象"""
        return datetime.fromisoformat(self.datetime_iso)


def parse_time_from_natural_language(user_input: str) -> CalendarReminder:
    """
    使用 LLM 从自然语言中提取时间信息

    Args:
        user_input: 用户输入（如："明天上午八点提醒我拿充电器"）

    Returns:
        CalendarReminder 对象

    Raises:
        ValueError: 如果无法解析时间
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    next_week = now + timedelta(days=7)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是时间提取专家。从用户输入中提取日历提醒信息。

当前时间：{current_time}
当前日期：{current_date}
明天日期：{tomorrow_date}
下周日期：{next_week_date}

请提取：
1. summary：提醒内容（简洁明了，去掉"提醒我"等词）
2. datetime_iso：提醒时间（ISO 8601格式：YYYY-MM-DDTHH:MM:SS）
3. reminder_minutes：提前提醒时间（分钟，默认10分钟）
4. duration_minutes：事件持续时间（分钟，默认30分钟）

时间转换规则：
- "明天" = {tomorrow_date}
- "后天" = {tomorrow_date} + 1天
- "下周" = {next_week_date}
- "上午X点" = T0X:00:00（如上午8点 = T08:00:00）
- "下午X点" = T(X+12):00:00（如下午3点 = T15:00:00）
- "晚上八点" = T20:00:00
- "中午" = T12:00:00
- "如果只说"明天"没说具体时间，默认上午9点

提醒时间提取：
- 如果用户说"提前X分钟提醒"，提取X
- 如果用户说"提前半小时"，设置为30分钟
- 如果用户说"提前一小时"，设置为60分钟
- 否则使用默认10分钟

示例：
输入："明天上午八点提醒我拿充电器"
输出：
- summary: "拿充电器"
- datetime_iso: "{tomorrow_date}T08:00:00"
- reminder_minutes: 10
- duration_minutes: 30

输入："下周五下午三点开会，提前半小时提醒我"
输出：
- summary: "开会"
- datetime_iso: "{next_week_date}T15:00:00"（根据当前日期计算下周五）
- reminder_minutes: 30
- duration_minutes: 30
"""),
        ("user", "{user_input}")
    ])

    model = ChatOpenAI(
        model=config.AGENT_MODEL,
        base_url=config.OPENAI_API_BASE,
        api_key=config.OPENAI_API_KEY,
        temperature=0
    )

    chain = prompt | model.with_structured_output(CalendarReminder)

    try:
        result = chain.invoke({
            "user_input": user_input,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_date": now.date().isoformat(),
            "tomorrow_date": tomorrow.date().isoformat(),
            "next_week_date": next_week.date().isoformat()
        })

        # 验证时间是否在未来
        if result.start_time < now:
            raise ValueError(f"提醒时间 {result.start_time} 必须在未来")

        return result

    except Exception as e:
        raise ValueError(f"无法解析时间：{str(e)}")
