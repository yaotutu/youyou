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

    # Zep 记忆系统配置 (可选)
    ZEP_API_KEY: str = os.getenv("ZEP_API_KEY", "")  # Zep Cloud API Key
    ZEP_API_URL: str = os.getenv("ZEP_API_URL", "http://localhost:8000")  # 本地 Zep URL

    # CalDAV 日历配置
    CALDAV_URL: str = os.getenv("CALDAV_URL", "")
    CALDAV_USERNAME: str = os.getenv("CALDAV_USERNAME", "")
    CALDAV_PASSWORD: str = os.getenv("CALDAV_PASSWORD", "")
    CALDAV_CALENDAR_NAME: str = os.getenv("CALDAV_CALENDAR_NAME", "")
    CALDAV_DEFAULT_REMINDER_MINUTES: int = int(
        os.getenv("CALDAV_DEFAULT_REMINDER_MINUTES", "10")
    )

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
        masked_zep_key = '*' * 10 + cls.ZEP_API_KEY[-4:] if cls.ZEP_API_KEY else '未设置'
        masked_caldav_password = '*' * 10 + cls.CALDAV_PASSWORD[-4:] if cls.CALDAV_PASSWORD else '未设置'
        print("当前配置:")
        print(f"  API Base: {cls.OPENAI_API_BASE}")
        print(f"  API Key: {masked_key}")
        print(f"  路由模型: {cls.ROUTER_MODEL}")
        print(f"  Agent模型: {cls.AGENT_MODEL}")
        print(f"  用户ID: {cls.USER_ID}")
        print(f"  数据目录: {cls.DATA_DIR}")
        print(f"  Zep API Key: {masked_zep_key}")
        print(f"  Zep API URL: {cls.ZEP_API_URL}")
        print(f"  CalDAV URL: {cls.CALDAV_URL if cls.CALDAV_URL else '未设置'}")
        print(f"  CalDAV 用户名: {cls.CALDAV_USERNAME if cls.CALDAV_USERNAME else '未设置'}")
        print(f"  CalDAV 密码: {masked_caldav_password}")


# 全局配置实例
config = Config()
