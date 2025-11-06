"""调试 Agent 迭代次数"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from youyou.agents.note_agent.agent import note_agent

def test_simple_note():
    """测试简单笔记保存"""
    print("=" * 60)
    print("测试 1：简单笔记保存")
    print("=" * 60)

    query = "记一下：Python 装饰器很有用"
    print(f"\n输入: {query}\n")

    try:
        response = note_agent.invoke(query)
        print(f"\n✅ 响应:\n{response}\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

def test_github_url():
    """测试 GitHub URL"""
    print("\n" + "=" * 60)
    print("测试 2：GitHub URL 分析")
    print("=" * 60)

    query = "https://github.com/fastapi/fastapi"
    print(f"\n输入: {query}\n")

    try:
        response = note_agent.invoke(query)
        print(f"\n✅ 响应:\n{response[:500]}...\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # test_simple_note()
    test_github_url()
