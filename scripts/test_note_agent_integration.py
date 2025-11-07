"""测试 NoteAgent 与 Supervisor 的集成"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agents.supervisor.agent import supervisor


def test_supervisor_routes_to_note_agent():
    """测试 Supervisor 能否正确路由到 NoteAgent"""
    print("\n" + "=" * 60)
    print("测试：Supervisor 路由到 NoteAgent")
    print("=" * 60)

    test_cases = [
        "记一下：Rust 是一门系统编程语言，强调内存安全",
        "列出我的所有笔记",
        "搜索关于 Python 的笔记",
        # "分析项目：https://github.com/rustlang/rust",  # 需要网络，注释掉
    ]

    for query in test_cases:
        print(f"\n用户: {query}")
        print("-" * 60)

        try:
            result = supervisor.invoke({"messages": [{"role": "user", "content": query}]})

            # 提取响应
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    response = last_message.content
                else:
                    response = str(last_message)

                print(f"助手: {response[:200]}...")
            else:
                print("助手: [无响应]")

        except Exception as e:
            print(f"❌ 错误: {e}")

    print("\n" + "=" * 60)
    print("✅ 集成测试完成！")
    print("=" * 60)


def main():
    """运行集成测试"""
    print("🚀 开始测试 NoteAgent 与 Supervisor 的集成...")

    try:
        test_supervisor_routes_to_note_agent()
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
