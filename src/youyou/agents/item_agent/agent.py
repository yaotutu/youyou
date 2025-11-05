"""物品管理 Agent - 使用 LangChain 1.0"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from youyou.config import config
from .tools import remember_item_location, query_item_location, list_all_items
from .prompts import ITEM_SYSTEM_PROMPT


# 创建模型实例
item_model = ChatOpenAI(
    model=config.AGENT_MODEL,
    base_url=config.OPENAI_API_BASE,
    api_key=config.OPENAI_API_KEY,
    temperature=0,  # 工具调用需要确定性
)

# 创建 ItemAgent
item_agent = create_agent(
    model=item_model,
    tools=[remember_item_location, query_item_location, list_all_items],
    system_prompt=ITEM_SYSTEM_PROMPT
)
