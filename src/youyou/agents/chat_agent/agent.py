"""通用对话 Agent - 使用 LangChain 1.0"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from youyou.config import config
from .prompts import CHAT_SYSTEM_PROMPT


# 创建模型实例
chat_model = ChatOpenAI(
    model=config.AGENT_MODEL,
    base_url=config.OPENAI_API_BASE,
    api_key=config.OPENAI_API_KEY,
    temperature=0.7,  # 对话可以有创造性
)

# 创建 ChatAgent (不需要工具)
chat_agent = create_agent(
    model=chat_model,
    tools=[],
    system_prompt=CHAT_SYSTEM_PROMPT
)
