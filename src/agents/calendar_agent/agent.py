"""CalendarAgent - 日历提醒 Agent"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import config
from core.agent_base import BaseAgent, AgentRegistry
from .tools import get_calendar_tools
from .prompts import CALENDAR_SYSTEM_PROMPT


class CalendarAgent(BaseAgent):
    """日历提醒 Agent

    功能:
    - 添加日历提醒事件
    - 查询即将到来的提醒
    - 删除/修改提醒
    """

    def __init__(self):
        super().__init__(
            name="calendar_agent",
            description="""处理日历提醒相关的请求。

当用户想要:
- 添加提醒 (例如: "明天上午八点提醒我拿充电器")
- 查询提醒 (例如: "我今天有什么提醒?")
- 删除提醒 (例如: "取消明天的提醒")
- 管理日程安排

参数:
    query: 用户关于日历提醒的问题或指令

返回:
    日历提醒管理的处理结果"""
        )

        print(f"[{self.name}] 🚀 正在初始化...")

        # 检查 CalDAV 配置
        if not config.CALDAV_URL:
            print(f"[{self.name}] ⚠️ 警告：未配置 CalDAV，日历功能将不可用")
            print(f"[{self.name}] 💡 请在 .env 中配置 CALDAV_URL、CALDAV_USERNAME 和 CALDAV_PASSWORD")

        self.model = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0,
        )

        tools = get_calendar_tools()

        self.agent = create_agent(
            model=self.model,
            tools=tools,
            system_prompt=CALENDAR_SYSTEM_PROMPT
        )

        print(f"[{self.name}] 🔧 可用工具数量: {len(tools)}")
        print(f"[{self.name}] ✓ 初始化完成")

    def invoke(self, query: str) -> str:
        """处理日历提醒请求"""
        print(f"[{self.name}] 📅 处理查询: {query}")

        try:
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": query}]}
            )
            response = self._extract_response_from_result(result)
            print(f"[{self.name}] ✓ 响应: {response[:100]}...")
            return response
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"[{self.name}] ✗ {error_msg}")

            # 友好的错误提示
            if "CalDAV" in str(e) or "连接" in str(e):
                return (
                    f"❌ CalDAV 服务连接失败：{str(e)}\n\n"
                    "请检查以下配置：\n"
                    "1. .env 文件中的 CALDAV_URL、CALDAV_USERNAME、CALDAV_PASSWORD\n"
                    "2. CalDAV 服务器是否可访问\n"
                    "3. 用户名和密码是否正确（建议使用 App 专用密码）"
                )

            return f"❌ {error_msg}"


# 创建并注册 CalendarAgent 实例
calendar_agent = CalendarAgent()
AgentRegistry.register(calendar_agent)

__all__ = ["calendar_agent", "CalendarAgent"]
