"""测试 GitHub 项目检索功能"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from youyou.agents.note_agent.agent import note_agent


def test_search(query: str):
    """测试搜索"""
    print("\n" + "=" * 70)
    print(f"🔍 搜索：{query}")
    print("=" * 70)

    try:
        response = note_agent.invoke(query)
        print(f"\n结果:")
        print("-" * 70)
        print(response)
        print("-" * 70)
    except Exception as e:
        print(f"❌ 错误: {e}")


def main():
    """运行搜索测试"""
    print("🚀 GitHub 项目检索测试")
    print("=" * 70)

    # 测试各种搜索方式
    test_cases = [
        "我之前收藏的 FastAPI 项目在哪？",
        "查找关于 Python 的笔记",
        "列出所有 GitHub 项目",
        "搜索 Web 框架",
        "我想找个高性能的 API 框架",
    ]

    for query in test_cases:
        test_search(query)
        print("\n" + "▪" * 70 + "\n")


if __name__ == "__main__":
    main()
