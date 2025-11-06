"""NoteAgent - 笔记本 Agent - 使用 LangChain 1.0 + BaseAgent 接口"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from youyou.config import config
from youyou.core.agent_base import BaseAgent, AgentRegistry
from youyou.agents.note_agent.tools import get_note_agent_tools
from youyou.agents.note_agent.prompts import NOTE_AGENT_SYSTEM_PROMPT


class NoteAgent(BaseAgent):
    """笔记本 Agent

    功能:
    - 保存笔记（灵感、想法等）
    - 分析 GitHub 项目并保存
    - 搜索和检索笔记
    - 知识管理中枢
    """

    def __init__(self):
        super().__init__(
            name="note_agent",
            description="""处理笔记和知识管理相关的请求。

当用户想要:
- 保存笔记、灵感、想法 (例如: "记一下这个想法...")
- 分析 GitHub 项目 (例如: "https://github.com/...")
- 搜索笔记 (例如: "我之前收藏的 FastAPI 项目在哪?")
- 查看笔记列表 (例如: "列出我的所有笔记")

参数:
    query: 用户关于笔记的问题或指令

返回:
    笔记管理的处理结果"""
        )

        # 创建 LangChain Agent
        self.model = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0,
        )

        tools = get_note_agent_tools()

        self.agent = create_agent(
            model=self.model,
            tools=tools,
            system_prompt=NOTE_AGENT_SYSTEM_PROMPT
        )

    def invoke(self, query: str) -> str:
        """处理笔记相关请求

        Args:
            query: 用户的原始查询文本

        Returns:
            处理结果文本
        """
        print(f"[{self.name}] 📝 处理查询: {query}")

        try:
            # 增加递归限制到 50，避免复杂任务超出限制
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"recursion_limit": 50, "debug": True}  # 启用调试模式
            )
            response = self._extract_response_from_result(result)

            # 打印迭代次数统计
            if "messages" in result:
                print(f"[{self.name}] 📊 总消息数: {len(result['messages'])}")

            print(f"[{self.name}] ✓ 响应: {response[:100]}...")
            return response

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"[{self.name}] ✗ {error_msg}")
            return error_msg


# 创建并注册 NoteAgent 实例
note_agent = NoteAgent()
AgentRegistry.register(note_agent)

__all__ = ["note_agent", "NoteAgent"]
