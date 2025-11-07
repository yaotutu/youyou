"""测试导入"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"

print("测试1: 导入 config")
try:
    from config import config
    print("✓ config 导入成功")
except Exception as e:
    print(f"✗ config 导入失败: {e}")
    exit(1)

print("\n测试2: 导入 item_agent")
try:
    from agents.item_agent import item_agent
    print(f"✓ item_agent 导入成功: {type(item_agent)}")
except Exception as e:
    print(f"✗ item_agent 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n测试3: 导入 chat_agent")
try:
    from agents.chat_agent import chat_agent
    print(f"✓ chat_agent 导入成功: {type(chat_agent)}")
except Exception as e:
    print(f"✗ chat_agent 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n测试4: 导入 supervisor")
try:
    from agents.supervisor import supervisor
    print(f"✓ supervisor 导入成功: {type(supervisor)}")
except Exception as e:
    print(f"✗ supervisor 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ 所有导入测试通过!")
