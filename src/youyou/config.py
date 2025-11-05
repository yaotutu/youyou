"""配置管理模块

从环境变量加载配置,提供全局配置对象。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """全局配置类"""

    # OpenAI API 配置
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # 模型配置
    ROUTER_MODEL: str = os.getenv("ROUTER_MODEL", "gpt-3.5-turbo")
    AGENT_MODEL: str = os.getenv("AGENT_MODEL", "gpt-4")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

    # 系统配置
    USER_ID: str = os.getenv("USER_ID", "default")
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))

    # SQLite 数据库配置
    ITEMS_DB_PATH: Path = DATA_DIR / "items.db"

    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        if not cls.OPENAI_API_KEY:
            print("警告: 未设置 OPENAI_API_KEY 环境变量")
            return False

        # 确保数据目录存在
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

        return True

    @classmethod
    def display(cls) -> None:
        """显示当前配置(隐藏敏感信息)"""
        masked_key = '*' * 10 + cls.OPENAI_API_KEY[-4:] if cls.OPENAI_API_KEY else '未设置'
        print("当前配置:")
        print(f"  API Base: {cls.OPENAI_API_BASE}")
        print(f"  API Key: {masked_key}")
        print(f"  路由模型: {cls.ROUTER_MODEL}")
        print(f"  Agent模型: {cls.AGENT_MODEL}")
        print(f"  用户ID: {cls.USER_ID}")
        print(f"  数据目录: {cls.DATA_DIR}")


# 全局配置实例
config = Config()
