"""测试 Zep 记忆系统集成

测试场景:
1. 跨轮对话理解（代词引用）
2. Zep 兜底查询（非结构化物品提及）
3. 上下文推理
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "youyou"))

from core.zep_memory import get_zep_memory
from core.database import get_database
from config import config


def test_zep_basic():
    """测试 Zep 基础功能"""
    print("\n" + "=" * 60)
    print("测试 1: Zep 基础功能")
    print("=" * 60)

    zep = get_zep_memory()

    # 添加测试消息
    print("\n1. 添加测试消息...")
    success1 = zep.add_interaction(
        user_input="钥匙放在客厅桌上了",
        assistant_response="好的，我记住了：钥匙在客厅桌上"
    )
    print(f"   结果: {'✓ 成功' if success1 else '✗ 失败'}")

    success2 = zep.add_interaction(
        user_input="护照在卧室抽屉里",
        assistant_response="好的，我记住了：护照在卧室抽屉里"
    )
    print(f"   结果: {'✓ 成功' if success2 else '✗ 失败'}")

    # 获取上下文
    print("\n2. 获取最近对话上下文...")
    context = zep.get_recent_context(limit=5)
    print(f"   获取到 {len(context)} 条消息:")
    for i, msg in enumerate(context[-2:], 1):  # 只显示最后2条
        print(f"   [{i}] {msg['role']}: {msg['content'][:50]}...")

    # 语义搜索
    print("\n3. 测试语义搜索...")
    memories = zep.search_memory("钥匙的位置", limit=3)
    print(f"   找到 {len(memories)} 条相关记忆:")
    for i, mem in enumerate(memories, 1):
        print(f"   [{i}] {mem['role']}: {mem['content'][:50]}... (score: {mem['score']:.3f})")

    print("\n✓ Zep 基础功能测试完成")


def test_cross_turn_reference():
    """测试跨轮对话引用"""
    print("\n" + "=" * 60)
    print("测试 2: 跨轮对话引用")
    print("=" * 60)

    zep = get_zep_memory()

    # 模拟对话
    print("\n模拟对话场景:")
    print("用户: 我买了一个蓝色的充电宝")
    zep.add_interaction(
        user_input="我买了一个蓝色的充电宝",
        assistant_response="听起来不错！"
    )

    print("用户: 放在背包侧袋了")
    zep.add_interaction(
        user_input="放在背包侧袋了",
        assistant_response="好的，我记住了"
    )

    # 测试引用理解
    print("\n测试引用查询:")
    print("用户: 那个蓝色的东西在哪？")

    memories = zep.search_memory("蓝色的东西 充电宝 位置", limit=3)
    print(f"\nZep 搜索结果 ({len(memories)} 条):")
    for i, mem in enumerate(memories, 1):
        print(f"  [{i}] {mem['content'][:80]}...")

    if memories:
        print("\n✓ 可以通过 Zep 找到相关信息")
    else:
        print("\n✗ 未找到相关信息")


def test_item_agent_zep_fallback():
    """测试 ItemAgent 的 Zep 兜底查询"""
    print("\n" + "=" * 60)
    print("测试 3: ItemAgent Zep 兜底查询")
    print("=" * 60)

    zep = get_zep_memory()
    db = get_database()

    # 场景: 用户在对话中提到物品，但没有明确记录到数据库
    print("\n1. 模拟非结构化物品提及...")
    print("   用户: 我的临时工牌放在车里了")
    zep.add_interaction(
        user_input="我的临时工牌放在车里了",
        assistant_response="知道了"
    )

    # 查询数据库（应该找不到）
    print("\n2. 尝试从 SQLite 查询...")
    result = db.query_item("临时工牌", user_id=config.USER_ID)
    print(f"   SQLite 结果: {result.get('status')}")

    # 使用 Zep 兜底
    if result.get('status') == 'not_found':
        print("\n3. SQLite 未找到，尝试 Zep 兜底...")
        memories = zep.search_memory("临时工牌 位置 放在", limit=3)
        print(f"   Zep 找到 {len(memories)} 条记忆:")
        for i, mem in enumerate(memories, 1):
            print(f"   [{i}] {mem['content']}")

        if memories:
            print("\n✓ Zep 兜底查询成功！")
        else:
            print("\n✗ Zep 也未找到")


def test_context_awareness():
    """测试上下文理解能力"""
    print("\n" + "=" * 60)
    print("测试 4: 上下文理解")
    print("=" * 60)

    zep = get_zep_memory()

    # 模拟上下文对话
    print("\n模拟对话:")
    conversations = [
        ("我准备去健身房", "好的，祝你锻炼愉快！"),
        ("运动耳机在哪？", "运动耳机在储物柜里"),
        ("水壶呢？", "水壶在厨房"),
    ]

    for user_msg, assistant_msg in conversations:
        print(f"  用户: {user_msg}")
        print(f"  助手: {assistant_msg}")
        zep.add_interaction(user_msg, assistant_msg)

    # 获取上下文
    print("\n获取对话上下文:")
    context = zep.get_recent_context(limit=6)
    print(f"  共 {len(context)} 条消息")

    # 测试摘要（如果可用）
    print("\n尝试获取会话摘要:")
    summary = zep.get_session_summary()
    if summary:
        print(f"  摘要: {summary[:100]}...")
    else:
        print("  摘要暂未生成（需要更多对话）")

    print("\n✓ 上下文理解测试完成")


def cleanup():
    """清理测试数据（可选）"""
    print("\n" + "=" * 60)
    print("注意: 测试数据已保存到 Zep 和 SQLite")
    print("如需清理，请手动删除数据库文件或 Zep session")
    print("=" * 60)


def main():
    """运行所有测试"""
    print("\n🧪 Zep 集成测试开始")
    print("=" * 60)
    print(f"User ID: {config.USER_ID}")
    print(f"Zep URL: {config.ZEP_API_URL}")
    print("=" * 60)

    try:
        # 运行测试
        test_zep_basic()
        test_cross_turn_reference()
        test_item_agent_zep_fallback()
        test_context_awareness()

        # 清理提示
        cleanup()

        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
