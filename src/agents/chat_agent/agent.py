"""通用对话 Agent - 使用 LangChain 1.0 + BaseAgent 接口"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import config
from core.agent_base import BaseAgent, AgentRegistry
from .prompts import CHAT_SYSTEM_PROMPT


class ChatAgent(BaseAgent):
    """通用对话 Agent

    功能:
    - 处理日常对话
    - 回答一般性问题
    - 提供建议和帮助
    """

    def __init__(self):
        super().__init__(
            name="chat_agent",
            description="""处理一般性对话和问题。

当用户进行:
- 日常对话 (例如: "你好", "今天天气怎么样")
- 一般性问题 (例如: "什么是人工智能?")
- 需要建议和帮助 (例如: "如何学习编程?")

参数:
    query: 用户的对话或问题

返回:
    对话的回复"""
        )

        # 创建 LangChain Agent
        self.model = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0.7,  # 对话可以有创造性
        )

        self.agent = create_agent(
            model=self.model,
            tools=[],  # ChatAgent 不需要工具
            system_prompt=CHAT_SYSTEM_PROMPT
        )

    def invoke(self, query: str) -> str:
        """处理对话请求

        Args:
            query: 用户的原始查询文本

        Returns:
            对话回复文本
        """
        print(f"[{self.name}] 📝 处理查询: {query}")

        try:
            result = self.agent.invoke({"messages": [{"role": "user", "content": query}]})
            response = self._extract_response_from_result(result)

            print(f"[{self.name}] ✓ 响应: {response[:100]}...")
            return response

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"[{self.name}] ✗ {error_msg}")
            return error_msg


# 创建并注册 ChatAgent 实例
chat_agent = ChatAgent()
AgentRegistry.register(chat_agent)

# 为了向后兼容,导出 LangChain agent (旧代码可能直接使用)
__all__ = ["chat_agent", "ChatAgent"]
