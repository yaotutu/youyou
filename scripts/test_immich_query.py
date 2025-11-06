"""快速测试：查询已保存的 immich 内容"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from agents.note_agent.agent import note_agent


def test_immich_query():
    """测试查询 immich"""
    print("=" * 70)
    print("测试: 给我讲讲 immich 这个")
    print("=" * 70)
    print()
    print("期望行为: 搜索笔记本里已保存的 immich 内容")
    print("不应该行为: 去 GitHub 分析新的 immich 项目")
    print()
    print("-" * 70)

    query = "给我讲讲 immich 这个"

    try:
        response = note_agent.invoke(query)

        print("\n" + "=" * 70)
        print("响应内容:")
        print("=" * 70)
        print(response)
        print()

        # 检查是否包含分析项目的日志
        print("\n" + "=" * 70)
        print("验证:")
        print("=" * 70)
        print("✓ 如果上面的日志中:")
        print("  - 有 'search_notes' 或类似搜索操作 → ✅ 正确")
        print("  - 有 'analyze_github_project' → ❌ 错误（不应该分析新项目）")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_immich_query()
