"""Agent 基础接口定义

定义所有子 Agent 必须实现的标准接口,实现 Agent 的自动注册和统一调用。
"""
from typing import Protocol, Dict, Any, List, runtime_checkable
from abc import ABC, abstractmethod
from langchain_core.tools import tool

from core.logger import logger


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

    def invoke(self, query: str) -> str:
        """处理用户请求

        Args:
            query: 用户的原始查询文本

        Returns:
            处理结果文本
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
    def invoke(self, query: str) -> str:
        """子类必须实现的核心处理逻辑"""
        pass

    @staticmethod
    def _extract_response_from_result(result: Dict[str, Any], default: str = "处理失败") -> str:
        """从 LangChain Agent 返回结果中提取响应文本

        这是一个通用的消息提取方法,适用于所有使用 create_agent 的子 Agent。

        Args:
            result: LangChain Agent 的 invoke 返回值
            default: 提取失败时的默认返回值

        Returns:
            提取的响应文本
        """
        # 提取最后一条消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return last_message.content
            elif isinstance(last_message, dict):
                return last_message.get("content", default)
            else:
                return default
        else:
            return default

    def as_tool(self):
        """将 Agent 包装为 LangChain Tool

        这个方法自动为每个 Agent 生成一个工具函数,
        Supervisor 可以直接使用,无需手写包装代码。
        """
        agent_instance = self
        agent_description = self.description

        @tool
        def agent_tool(query: str) -> str:
            """Agent tool generated from BaseAgent"""
            # 使用闭包捕获 agent_instance
            return agent_instance.invoke(query)

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
