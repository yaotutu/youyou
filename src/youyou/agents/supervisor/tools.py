"""Supervisor Agent 的工具 - 包装子 Agent"""
from langchain_core.tools import tool

from youyou.agents.item_agent import item_agent
from youyou.agents.chat_agent import chat_agent


@tool
def item_agent_tool(query: str) -> str:
    """处理物品位置相关的请求

    当用户想要:
    - 记录物品位置 (例如: "钥匙在客厅桌上")
    - 查询物品位置 (例如: "钥匙在哪?")
    - 列出所有物品 (例如: "我记录了哪些物品?")

    Args:
        query: 用户关于物品位置的问题或指令

    Returns:
        物品管理的处理结果
    """
    print(f"\n[Supervisor] 🔀 路由到 ItemAgent")
    print(f"[Supervisor] 📝 查询内容: {query}")
    print(f"[Supervisor] ⏳ 调用 ItemAgent 处理...")

    result = item_agent.invoke({"messages": [{"role": "user", "content": query}]})

    # 从 result 中提取最后一条消息
    messages = result.get("messages", [])
    print(f"[Supervisor] 📨 ItemAgent 返回消息数: {len(messages)}")

    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            response = last_message.content
        elif isinstance(last_message, dict):
            response = last_message.get("content", "处理失败")
        else:
            response = "处理失败"
    else:
        response = "处理失败"

    print(f"[Supervisor] ✓ ItemAgent 响应: {response[:100]}...")
    return response


@tool
def chat_agent_tool(query: str) -> str:
    """处理一般性对话和问题

    当用户进行:
    - 日常对话 (例如: "你好", "今天天气怎么样")
    - 一般性问题 (例如: "什么是人工智能?")
    - 需要建议和帮助 (例如: "如何学习编程?")

    Args:
        query: 用户的对话或问题

    Returns:
        对话的回复
    """
    print(f"\n[Supervisor] 🔀 路由到 ChatAgent")
    print(f"[Supervisor] 📝 查询内容: {query}")
    print(f"[Supervisor] ⏳ 调用 ChatAgent 处理...")

    result = chat_agent.invoke({"messages": [{"role": "user", "content": query}]})

    # 从 result 中提取最后一条消息
    messages = result.get("messages", [])
    print(f"[Supervisor] 📨 ChatAgent 返回消息数: {len(messages)}")

    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            response = last_message.content
        elif isinstance(last_message, dict):
            response = last_message.get("content", "处理失败")
        else:
            response = "处理失败"
    else:
        response = "处理失败"

    print(f"[Supervisor] ✓ ChatAgent 响应: {response[:100]}...")
    return response
