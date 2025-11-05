"""记忆管理模块

使用 mem0 提供智能记忆存储和检索功能。
"""
from typing import List, Dict, Any, Optional
from youyou.config import config


class MemoryManager:
    """记忆管理器 - 封装 mem0 功能"""

    def __init__(self):
        """初始化记忆系统"""
        self.memory = None
        self._initialized = False

    def _ensure_initialized(self):
        """延迟初始化记忆系统"""
        if self._initialized:
            return

        try:
            from mem0 import Memory
            import os

            # 设置环境变量,让 mem0 使用正确的 API
            os.environ["OPENAI_BASE_URL"] = config.OPENAI_API_BASE

            print(f"[记忆系统] 开始初始化...")
            print(f"[记忆系统] Qdrant 路径: {config.DATA_DIR / 'qdrant'}")
            print(f"[记忆系统] LLM 模型: {config.AGENT_MODEL}")
            print(f"[记忆系统] 嵌入模型: {config.EMBEDDING_MODEL}")
            print(f"[记忆系统] API Base: {config.OPENAI_API_BASE}")

            mem0_config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "youyou_memory",
                        "path": str(config.DATA_DIR / "qdrant"),
                    }
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": config.AGENT_MODEL,
                        "api_key": config.OPENAI_API_KEY,
                        "openai_base_url": config.OPENAI_API_BASE
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": config.EMBEDDING_MODEL,
                        "api_key": config.OPENAI_API_KEY,
                        "openai_base_url": config.OPENAI_API_BASE
                    }
                }
            }

            self.memory = Memory.from_config(mem0_config)
            print(f"[记忆系统] ✓ 初始化成功")
            self._initialized = True
        except Exception as e:
            print(f"[记忆系统] ✗ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            print("[记忆系统] 将在首次使用时重试...")
            self._initialized = False

    def add(
        self,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """添加记忆"""
        self._ensure_initialized()
        if not self.memory:
            return {"status": "error", "message": "记忆系统未初始化"}

        user_id = user_id or config.USER_ID

        try:
            result = self.memory.add(
                messages=content,
                user_id=user_id,
                metadata=metadata or {}
            )
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        self._ensure_initialized()
        if not self.memory:
            return []

        user_id = user_id or config.USER_ID

        try:
            results = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            # mem0 返回 {'results': [...]} 格式，需要提取 results 字段
            if isinstance(results, dict) and 'results' in results:
                return results['results']
            return results if results else []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def get_all(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        self._ensure_initialized()
        if not self.memory:
            return []

        user_id = user_id or config.USER_ID

        try:
            results = self.memory.get_all(user_id=user_id)
            # mem0 可能返回 {'results': [...]} 格式，需要提取 results 字段
            if isinstance(results, dict) and 'results' in results:
                return results['results']
            return results if results else []
        except Exception as e:
            print(f"获取记忆失败: {e}")
            return []

    def delete(self, memory_id: str) -> bool:
        """删除指定记忆"""
        self._ensure_initialized()
        if not self.memory:
            return False

        try:
            self.memory.delete(memory_id=memory_id)
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False


# 全局记忆管理器实例
memory_manager = MemoryManager()
