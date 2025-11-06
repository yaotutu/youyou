"""端到端测试 GitHub 分析（通过 NoteAgent）"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from agents.note_agent.agent import note_agent

def test_github_via_agent():
    """通过 NoteAgent 测试 GitHub 分析"""
    print("=" * 60)
    print("端到端测试：通过 NoteAgent 分析 GitHub 项目")
    print("=" * 60)

    test_url = "https://github.com/fastapi/fastapi"

    print(f"\n📥 测试 URL: {test_url}")
    print("-" * 60)
    print("⚙️  调用 NoteAgent.invoke()...")
    print()

    try:
        response = note_agent.invoke(test_url)
        print(f"\n✅ 成功！\n")
        print("响应内容:")
        print("-" * 60)
        print(response)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_github_via_agent()
