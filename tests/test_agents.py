"""测试 Agent 系统"""
import os
os.environ["OPENAI_API_KEY"] = "sk-test"
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"

from youyou.agents.supervisor import supervisor

def test_chat():
    """测试对话功能"""
    print("测试1: 对话功能")
    try:
        result = supervisor.invoke({"input": "你好"})
        print(f"✓ 对话测试通过: {result.get('output', 'N/A')}\n")
    except Exception as e:
        print(f"✗ 对话测试失败: {e}\n")

def test_item():
    """测试物品管理功能"""
    print("测试2: 物品管理功能")
    try:
        # 测试记录物品
        result = supervisor.invoke({"input": "钥匙在客厅桌上"})
        print(f"✓ 记录物品测试通过: {result.get('output', 'N/A')}\n")
    except Exception as e:
        print(f"✗ 记录物品测试失败: {e}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("YouYou Agent 系统测试")
    print("=" * 50 + "\n")
    
    test_chat()
    test_item()
    
    print("=" * 50)
    print("测试完成!")
    print("=" * 50)
