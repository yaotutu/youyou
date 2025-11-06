"""详细测试：查询 immich（检查是否会触发 analyze_github_project）"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from youyou.agents.note_agent.agent import note_agent


def test_immich_query_detailed():
    """测试查询 immich - 检测工具调用"""
    print("=" * 70)
    print("详细测试: 给我讲讲 immich 这个")
    print("=" * 70)
    print()
    print("🎯 检查目标:")
    print("  ✅ 应该：调用 search_notes")
    print("  ❌ 不应该：调用 analyze_github_project")
    print()
    print("-" * 70)

    query = "给我讲讲 immich 这个"

    # 记录开始
    print(f"\n🚀 开始处理查询: {query}")
    print()

    try:
        response = note_agent.invoke(query)

        print("\n" + "=" * 70)
        print("响应内容（前 300 字）:")
        print("=" * 70)
        print(response[:300])
        if len(response) > 300:
            print("...\n")

        print("\n" + "=" * 70)
        print("🔍 日志分析")
        print("=" * 70)
        print("请检查上面的完整日志，确认:")
        print("  1. 是否有 'search_notes' 或搜索相关的调用")
        print("  2. 是否有 '[analyze_github_project]' 日志")
        print("  3. 是否有 '[GitHub 分析器]' 日志")
        print()
        print("如果看到第 2 或 3 条，说明 Agent 违规调用了 analyze_github_project")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_immich_query_detailed()
