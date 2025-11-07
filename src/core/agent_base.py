"""Agent 基础接口定义

定义所有子 Agent 必须实现的标准接口,实现 Agent 的自动注册和统一调用。
"""
from typing import Protocol, Dict, Any, List, runtime_checkable
from abc import ABC, abstractmethod
from langchain_core.tools import tool
import json

from core.logger import logger
from core.response_types import AgentResponse, Action


@runtime_checkable
class AgentProtocol(Protocol):
    """Agent 协议 - 定义所有 Agent 必须实现的接口"""

    @property
    def name(self) -> str:
        """Agent 名称,用于日志和注册"""
        ...

    @property
    def description(self) -> str:
        """Agent 功能描述,用于 Supervisor 路由决策"""
        ...

    def invoke(self, query: str) -> AgentResponse:
        """处理用户请求

        Args:
            query: 用户的原始查询文本

        Returns:
            结构化响应对象
        """
        ...


class BaseAgent(ABC):
    """Agent 基类 - 提供默认实现和工具生成"""

    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @abstractmethod
    def invoke(self, query: str) -> AgentResponse:
        """子类必须实现的核心处理逻辑"""
        pass

    def _extract_response_from_result(self, result: Dict[str, Any]) -> AgentResponse:
        """从 LangChain Agent 返回结果中提取结构化响应

        这个方法会：
        1. 从所有 ToolMessage 中提取结构化数据（action_type 和 data）
        2. 提取最终的文本消息
        3. 构造 AgentResponse 对象

        Args:
            result: LangChain Agent 的 invoke 返回值

        Returns:
            结构化响应对象
        """
        from langchain_core.messages import ToolMessage

        messages = result.get("messages", [])
        actions = []
        final_message = ""

        # 1. 提取所有 ToolMessage 中的结构化数据
        for msg in messages:
            if isinstance(msg, ToolMessage):
                try:
                    # ToolMessage.content 是 JSON 字符串（LangChain 自动序列化的）
                    tool_data = json.loads(msg.content)

                    # 如果工具返回了 action_type 和 data，则提取
                    if "action_type" in tool_data and "data" in tool_data:
                        actions.append(Action(
                            type=tool_data["action_type"],
                            data=tool_data["data"]
                        ))
                except (json.JSONDecodeError, KeyError, TypeError):
                    # 工具返回的不是结构化数据，忽略
                    logger.debug(f"[{self.name}] ⚠️ 工具返回非结构化数据: {msg.content[:100]}")
                    pass

        # 2. 提取最终回复文本
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                final_message = last_message.content
            elif isinstance(last_message, dict):
                final_message = last_message.get("content", "")
            else:
                final_message = str(last_message)

        # 如果没有文本消息，使用默认消息
        if not final_message:
            final_message = "处理完成"

        # 3. 如果没有任何 action，生成一个默认的 chat_response
        if not actions:
            actions.append(Action(
                type="chat_response",
                data={"text": final_message}
            ))

        return AgentResponse(
            success=True,
            agent=self.name,
            message=final_message,
            actions=actions
        )

    def as_tool(self):
        """将 Agent 包装为 LangChain Tool

        这个方法自动为每个 Agent 生成一个工具函数,
        Supervisor 可以直接使用,无需手写包装代码。

        工具函数返回 dict（包含结构化数据），LangChain 会自动序列化为 JSON。
        """
        agent_instance = self
        agent_description = self.description

        @tool
        def agent_tool(query: str) -> dict:
            """Agent tool generated from BaseAgent"""
            # 调用 Agent 的 invoke 方法，返回 AgentResponse 对象
            agent_response = agent_instance.invoke(query)

            # 将 AgentResponse 转换为 dict，供 LangChain 序列化
            return {
                "agent": agent_response.agent,
                "message": agent_response.message,
                "success": agent_response.success,
                "actions": [
                    {"type": a.type, "data": a.data}
                    for a in agent_response.actions
                ]
            }

        # 动态设置工具的名称和描述
        agent_tool.name = f"{self.name}_tool"
        agent_tool.description = agent_description

        return agent_tool


class AgentRegistry:
    """Agent 注册中心

    所有子 Agent 必须在这里注册,Supervisor 从这里自动获取所有可用的 Agent。
    """

    _agents: Dict[str, AgentProtocol] = {}

    @classmethod
    def register(cls, agent: AgentProtocol) -> None:
        """注册一个 Agent

        Args:
            agent: 实现了 AgentProtocol 的 Agent 实例

        Raises:
            TypeError: 如果 agent 未实现 AgentProtocol
        """
        if not isinstance(agent, AgentProtocol):
            raise TypeError(f"{agent} 必须实现 AgentProtocol 接口")

        cls._agents[agent.name] = agent
        logger.info(f"[注册中心] ✓ 注册 Agent: {agent.name}")

    @classmethod
    def get_all_agents(cls) -> List[AgentProtocol]:
        """获取所有已注册的 Agent"""
        return list(cls._agents.values())

    @classmethod
    def get_all_tools(cls) -> List:
        """获取所有 Agent 的工具列表

        Supervisor 调用此方法获取所有子 Agent 的工具,
        无需手动维护工具列表。
        """
        tools = []
        for agent in cls._agents.values():
            if isinstance(agent, BaseAgent):
                tools.append(agent.as_tool())
            else:
                # 对于不继承 BaseAgent 的 Agent,需要手动实现 as_tool
                raise NotImplementedError(
                    f"{agent.name} 必须继承 BaseAgent 或实现 as_tool() 方法"
                )
        return tools

    @classmethod
    def clear(cls) -> None:
        """清空所有注册的 Agent (主要用于测试)"""
        cls._agents.clear()
