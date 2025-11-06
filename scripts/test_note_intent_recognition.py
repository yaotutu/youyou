"""测试 NoteAgent 意图识别 - 查询 vs 分析"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from youyou.agents.note_agent.agent import note_agent


def test_intent(query: str, expected_behavior: str):
    """测试意图识别"""
    print("\n" + "=" * 70)
    print(f"📝 查询: {query}")
    print(f"🎯 期望行为: {expected_behavior}")
    print("=" * 70)

    try:
        response = note_agent.invoke(query)
        print("\n✅ 响应:")
        print("-" * 70)
        print(response[:500])
        if len(response) > 500:
            print("...")
        print("-" * 70)
        return True
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行意图识别测试"""
    print("🚀 NoteAgent 意图识别测试")
    print("=" * 70)
    print("目标: 确保 Agent 能正确区分 '查询已保存内容' vs '分析新项目'")
    print()

    test_cases = [
        {
            "query": "给我讲讲 immich 这个",
            "expected": "搜索笔记本里的 immich 内容（不应该去分析新项目）"
        },
        {
            "query": "我之前收藏的 FastAPI 是什么",
            "expected": "搜索笔记本里的 FastAPI 内容"
        },
        {
            "query": "介绍一下我保存的那个 Immich Power Tools",
            "expected": "搜索笔记本里的 Immich Power Tools"
        },
        {
            "query": "https://github.com/fastapi/fastapi",
            "expected": "分析这个 GitHub 项目（因为是完整 URL）"
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 70}")
        print(f"# 测试 {i}/{len(test_cases)}")
        print(f"{'#' * 70}")

        if test_intent(test_case["query"], test_case["expected"]):
            passed += 1
        else:
            failed += 1

        print("\n💡 请手动验证响应是否符合期望行为")
        input("按 Enter 继续下一个测试...")

    # 总结
    print("\n\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总计: {len(test_cases)} 个测试")
    print(f"✅ 完成: {passed}")
    print(f"❌ 失败: {failed}")

    if failed == 0:
        print("\n🎉 所有测试完成！请手动验证结果是否符合预期。")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")


if __name__ == "__main__":
    main()
