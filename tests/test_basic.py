"""基础功能测试脚本"""

# 测试导入
try:
    from youyou.config import config
    print("✅ Config 模块导入成功")
except Exception as e:
    print(f"❌ Config 模块导入失败: {e}")

try:
    from youyou.core.router import LLMRouter
    print("✅ Router 模块导入成功")
except Exception as e:
    print(f"❌ Router 模块导入失败: {e}")

try:
    from youyou.core.memory import memory_manager
    print("✅ Memory 模块导入成功")
except Exception as e:
    print(f"❌ Memory 模块导入失败: {e}")

try:
    from youyou.agents.item_agent import item_agent
    print("✅ ItemAgent 导入成功")
except Exception as e:
    print(f"❌ ItemAgent 导入失败: {e}")

try:
    from youyou.agents.chat_agent import chat_agent
    print("✅ ChatAgent 导入成功")
except Exception as e:
    print(f"❌ ChatAgent 导入失败: {e}")

try:
    from youyou.tools.item_tools import remember_item_location, query_item_location
    print("✅ ItemTools 导入成功")
except Exception as e:
    print(f"❌ ItemTools 导入失败: {e}")

print("\n所有模块导入测试完成!")
