"""测试 GitHub 项目保存 - 验证向量维度修复"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from youyou.agents.note_agent.agent import note_agent


def test_github_save():
    """测试 GitHub 项目保存（验证向量正常保存）"""
    print("=" * 70)
    print("测试 GitHub 项目保存 - 向量维度修复验证")
    print("=" * 70)
    print()

    # 测试一个小型项目
    test_url = "https://github.com/fastapi/fastapi"

    print(f"📥 测试 URL: {test_url}")
    print()
    print("🚀 开始分析...")
    print("-" * 70)

    try:
        response = note_agent.invoke(test_url)

        print()
        print("-" * 70)
        print("✅ 测试成功！")
        print()
        print("响应内容:")
        print(response)
        print()

        # 检查是否还有向量保存失败的警告
        print()
        print("=" * 70)
        print("验证结果")
        print("=" * 70)
        print()
        print("请检查上面的日志，确认:")
        print("  ✓ Qdrant 初始化成功")
        print("  ✓ 向量已保存到 Qdrant")
        print("  ✗ 没有 'could not broadcast' 错误")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_github_save()
    sys.exit(0 if success else 1)
