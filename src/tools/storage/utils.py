"""笔记工具函数"""
import hashlib
import json
import uuid
from typing import List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import Config
from core.logger import logger


class NoteUtils:
    """笔记工具类"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0
        )
        self.embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY
        )

    def extract_tags(self, title: str, content: str, max_tags: int = 5) -> List[str]:
        """
        使用 LLM 自动提取标签

        Args:
            title: 笔记标题
            content: 笔记内容
            max_tags: 最多提取的标签数量

        Returns:
            标签列表
        """
        # 截断过长的内容
        max_content_length = 1000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        prompt = f"""请为以下笔记提取 {max_tags} 个关键标签。

标题: {title}
内容: {content}

要求：
1. 标签应该是简短的关键词（1-3 个字）
2. 优先提取技术栈、领域、主题等
3. 以 JSON 数组格式返回，例如 ["Python", "AI", "工具"]

只返回 JSON 数组，不要其他内容。
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # 移除可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            tags = json.loads(content.strip())

            # 确保返回列表
            if not isinstance(tags, list):
                return []

            return tags[:max_tags]

        except Exception as e:
            logger.error(f"[笔记工具] 提取标签失败: {e}")
            return []

    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        try:
            vector = self.embeddings.embed_query(text)
            return vector
        except Exception as e:
            logger.error(f"[笔记工具] 生成向量失败: {e}")
            return []

    @staticmethod
    def generate_note_id(content: str) -> str:
        """
        生成笔记 ID（UUID 格式，基于内容生成确定性 ID）

        Args:
            content: 笔记内容

        Returns:
            UUID 格式的笔记 ID
        """
        # 使用内容的 SHA256 哈希生成确定性 UUID（UUID5）
        # 这样相同内容总是生成相同的 ID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, content))
