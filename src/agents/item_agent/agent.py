"""物品管理 Agent - 使用 LangChain 1.0 + BaseAgent 接口"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import config
from core.agent_base import BaseAgent, AgentRegistry
from core.logger import logger
from core.response_types import AgentResponse
from .tools import remember_item_location, query_item_location, list_all_items
from .prompts import ITEM_SYSTEM_PROMPT


class ItemAgent(BaseAgent):
    """物品位置管理 Agent

    功能:
    - 记录物品的存放位置
    - 查询物品的位置
    - 列出所有已记录的物品
    """

    def __init__(self):
        super().__init__(
            name="item_agent",
            description="""处理物品位置相关的请求。

当用户想要:
- 记录物品位置 (例如: "钥匙在客厅桌上")
- 查询物品位置 (例如: "钥匙在哪?")
- 列出所有物品 (例如: "我记录了哪些物品?")

参数:
    query: 用户关于物品位置的问题或指令

返回:
    物品管理的处理结果"""
        )

        # 创建 LangChain Agent
        self.model = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0,  # 工具调用需要确定性
        )

        self.agent = create_agent(
            model=self.model,
            tools=[remember_item_location, query_item_location, list_all_items],
            system_prompt=ITEM_SYSTEM_PROMPT
        )

    def invoke(self, query: str) -> AgentResponse:
        """处理物品位置相关请求

        Args:
            query: 用户的原始查询文本

        Returns:
            结构化响应对象
        """
        logger.info(f"[{self.name}] 📝 处理查询: {query}")

        try:
            result = self.agent.invoke({"messages": [{"role": "user", "content": query}]})
            agent_response = self._extract_response_from_result(result)

            logger.info(f"[{self.name}] ✓ 响应: {agent_response.message[:100]}...")
            return agent_response

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            logger.error(f"[{self.name}] ✗ {error_msg}")
            return AgentResponse.error_response(
                agent=self.name,
                error=error_msg
            )


# 创建并注册 ItemAgent 实例
item_agent = ItemAgent()
AgentRegistry.register(item_agent)

# 为了向后兼容,导出 LangChain agent (旧代码可能直接使用)
__all__ = ["item_agent", "ItemAgent"]
