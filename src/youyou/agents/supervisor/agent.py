"""Supervisor Agent - 协调子 Agent"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from youyou.config import config
from .tools import item_agent_tool, chat_agent_tool
from .prompts import SUPERVISOR_SYSTEM_PROMPT


# 创建模型实例
router_model = ChatOpenAI(
    model=config.ROUTER_MODEL,
    base_url=config.OPENAI_API_BASE,
    api_key=config.OPENAI_API_KEY,
    temperature=0,  # 路由决策需要确定性
)

# 创建 Supervisor Agent
supervisor = create_agent(
    model=router_model,
    tools=[item_agent_tool, chat_agent_tool],
    system_prompt=SUPERVISOR_SYSTEM_PROMPT
)
