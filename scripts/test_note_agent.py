"""测试 NoteAgent 功能"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from config import Config
from agents.note_agent.agent import note_agent


def test_save_note():
    """测试保存普通笔记"""
    print("\n" + "=" * 60)
    print("测试 1：保存普通笔记")
    print("=" * 60)

    query = "记一下：Python 的装饰器可以用来实现缓存、日志记录、权限验证等功能，非常强大。"
    result = note_agent.invoke(query)
    print(f"\n结果：\n{result}")


def test_save_github_project():
    """测试分析 GitHub 项目"""
    print("\n" + "=" * 60)
    print("测试 2：分析 GitHub 项目")
    print("=" * 60)

    query = "帮我分析这个项目：https://github.com/langchain-ai/langchain"
    result = note_agent.invoke(query)
    print(f"\n结果：\n{result}")


def test_search_notes():
    """测试搜索笔记"""
    print("\n" + "=" * 60)
    print("测试 3：搜索笔记")
    print("=" * 60)

    query = "我之前记录的关于 Python 装饰器的笔记在哪？"
    result = note_agent.invoke(query)
    print(f"\n结果：\n{result}")


def test_list_notes():
    """测试列出笔记"""
    print("\n" + "=" * 60)
    print("测试 4：列出所有笔记")
    print("=" * 60)

    query = "列出我的所有笔记"
    result = note_agent.invoke(query)
    print(f"\n结果：\n{result}")


def test_list_github_projects():
    """测试列出 GitHub 项目笔记"""
    print("\n" + "=" * 60)
    print("测试 5：列出 GitHub 项目笔记")
    print("=" * 60)

    query = "列出我收藏的所有 GitHub 项目"
    result = note_agent.invoke(query)
    print(f"\n结果：\n{result}")


def main():
    """运行所有测试"""
    print("🚀 开始测试 NoteAgent...")
    print(f"配置信息：")
    config = Config()
    print(f"  - 模型: {config.AGENT_MODEL}")
    print(f"  - 数据目录: {config.DATA_DIR}")

    try:
        # 测试 1：保存笔记
        test_save_note()

        # 测试 2：分析 GitHub 项目（这个可能需要网络，较慢）
        # test_save_github_project()

        # 测试 3：搜索笔记
        test_search_notes()

        # 测试 4：列出笔记
        test_list_notes()

        # 测试 5：列出 GitHub 项目
        # test_list_github_projects()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
