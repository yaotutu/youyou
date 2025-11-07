"""Supervisor Agent - 使用 LangChain 1.0 + 自动注册系统"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import config
from core.agent_base import AgentRegistry
from .prompts import SUPERVISOR_SYSTEM_PROMPT

# 导入所有子 Agent 以触发注册
# 每个子 Agent 在导入时会自动调用 AgentRegistry.register()
from agents.item_agent import item_agent  # noqa: F401
from agents.chat_agent import chat_agent  # noqa: F401
from agents.note_agent import note_agent  # noqa: F401
from agents.calendar_agent import calendar_agent  # noqa: F401


def create_supervisor():
    """创建 Supervisor Agent

    自动从 AgentRegistry 获取所有已注册的子 Agent 工具,
    无需手动维护工具列表。

    Returns:
        配置好的 Supervisor Agent
    """
    print("\n[Supervisor] 🚀 初始化...")

    # 创建模型实例
    supervisor_model = ChatOpenAI(
        model=config.ROUTER_MODEL,
        base_url=config.OPENAI_API_BASE,
        api_key=config.OPENAI_API_KEY,
        temperature=0,  # 路由决策需要确定性
    )

    # 从注册中心自动获取所有子 Agent 的工具
    tools = AgentRegistry.get_all_tools()

    print(f"[Supervisor] 📋 已注册的 Agent:")
    for agent in AgentRegistry.get_all_agents():
        print(f"  - {agent.name}: {agent.description.split('.')[0]}...")

    print(f"[Supervisor] 🔧 可用工具数量: {len(tools)}")

    # 创建 Supervisor Agent
    supervisor = create_agent(
        model=supervisor_model,
        tools=tools,  # 自动获取的工具列表
        system_prompt=SUPERVISOR_SYSTEM_PROMPT
    )

    print("[Supervisor] ✓ 初始化完成\n")
    return supervisor


# 创建 Supervisor 实例
supervisor = create_supervisor()

__all__ = ["supervisor", "create_supervisor"]
