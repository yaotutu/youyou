"""调试 GitHub 分析问题"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from config import Config
from agents.note_agent.github_analyzer import GitHubAnalyzer

def test_github_analyzer():
    """直接测试 GitHub 分析器"""
    print("=" * 60)
    print("测试 GitHub 分析器（绕过 Agent）")
    print("=" * 60)

    config = Config()
    analyzer = GitHubAnalyzer(config)

    test_url = "https://github.com/fastapi/fastapi"

    print(f"\n📥 测试 URL: {test_url}")
    print("-" * 60)

    try:
        result = analyzer.analyze_repo(test_url)

        if result:
            print("\n✅ 分析成功！\n")
            print(f"项目名: {result['metadata']['full_name']}")
            print(f"描述: {result['metadata']['description']}")
            print(f"Stars: {result['metadata']['stars']}")
            print(f"语言: {result['metadata']['language']}")
            print(f"\n分析结果:")
            print(f"  - 用途: {result['analysis']['purpose']}")
            print(f"  - 技术栈: {result['analysis']['tech_stack']}")
            print(f"  - 核心功能: {result['analysis']['key_features'][:2] if result['analysis']['key_features'] else '无'}")
        else:
            print("\n❌ 分析失败：返回 None")

    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_github_analyzer()
