"""基础功能测试脚本"""

# 测试导入
try:
    from config import config
    print("✅ Config 模块导入成功")
except Exception as e:
    print(f"❌ Config 模块导入失败: {e}")

try:
    from core.database import get_database
    print("✅ Database 模块导入成功")
except Exception as e:
    print(f"❌ Database 模块导入失败: {e}")

try:
    from agents.item_agent import item_agent
    print("✅ ItemAgent 导入成功")
except Exception as e:
    print(f"❌ ItemAgent 导入失败: {e}")

try:
    from agents.chat_agent import chat_agent
    print("✅ ChatAgent 导入成功")
except Exception as e:
    print(f"❌ ChatAgent 导入失败: {e}")

try:
    from tools.item_tools import remember_item_location, query_item_location
    print("✅ ItemTools 导入成功")
except Exception as e:
    print(f"❌ ItemTools 导入失败: {e}")

print("\n所有模块导入测试完成!")
