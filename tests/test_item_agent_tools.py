"""测试 ItemAgent 的工具调用"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from youyou.agents.item_agent import item_agent


def test_remember_tool_call():
    """测试记录工具是否被正确调用"""
    print("\n" + "=" * 60)
    print("测试: ItemAgent 记录物品位置")
    print("=" * 60)

    result = item_agent.invoke({
        "messages": [{"role": "user", "content": "钥匙放在书桌抽屉里"}]
    })

    print(f"\n返回的消息数量: {len(result.get('messages', []))}")
    for i, msg in enumerate(result.get('messages', [])):
        msg_type = type(msg).__name__
        content = getattr(msg, 'content', str(msg))
        print(f"\n消息 [{i}] - {msg_type}:")
        print(f"内容: {content}")

        # 检查是否有 tool_calls
        if hasattr(msg, 'tool_calls'):
            print(f"工具调用: {msg.tool_calls}")

        # 检查是否有 additional_kwargs
        if hasattr(msg, 'additional_kwargs'):
            print(f"额外信息: {msg.additional_kwargs}")

    print("\n" + "=" * 60)


def test_query_tool_call():
    """测试查询工具是否被正确调用"""
    print("\n" + "=" * 60)
    print("测试: ItemAgent 查询物品位置")
    print("=" * 60)

    result = item_agent.invoke({
        "messages": [{"role": "user", "content": "钥匙在哪里？"}]
    })

    print(f"\n返回的消息数量: {len(result.get('messages', []))}")
    for i, msg in enumerate(result.get('messages', [])):
        msg_type = type(msg).__name__
        content = getattr(msg, 'content', str(msg))
        print(f"\n消息 [{i}] - {msg_type}:")
        print(f"内容: {content}")

        # 检查是否有 tool_calls
        if hasattr(msg, 'tool_calls'):
            print(f"工具调用: {msg.tool_calls}")

        # 检查是否有 additional_kwargs
        if hasattr(msg, 'additional_kwargs'):
            print(f"额外信息: {msg.additional_kwargs}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("开始测试 ItemAgent 工具调用...")
    test_remember_tool_call()
    test_query_tool_call()
    print("\n测试完成！")
