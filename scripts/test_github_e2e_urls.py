"""端到端测试 GitHub URL 分析（各种格式）"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from agents.note_agent.agent import note_agent


def test_github_analysis(url: str, description: str):
    """测试 GitHub URL 分析"""
    print("\n" + "=" * 70)
    print(f"测试: {description}")
    print("=" * 70)
    print(f"📥 URL: {url}\n")

    try:
        response = note_agent.invoke(url)
        print(f"\n✅ 成功！\n")
        print("响应内容:")
        print("-" * 70)
        print(response[:800] if len(response) > 800 else response)
        if len(response) > 800:
            print("...")
        print("-" * 70)
        return True
    except Exception as e:
        print(f"\n❌ 失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("🚀 GitHub URL 分析端到端测试")
    print("=" * 70)

    test_cases = [
        {
            "url": "https://github.com/fastapi/fastapi",
            "description": "仓库主页（标准格式）"
        },
        {
            "url": "https://github.com/fastapi/fastapi/tree/main/docs",
            "description": "子目录页面（应提取仓库）"
        },
        {
            "url": "https://github.com/fastapi/fastapi/blob/main/README.md",
            "description": "文件页面（应提取仓库）"
        },
        {
            "url": "fastapi/fastapi",
            "description": "简写格式"
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 70}")
        print(f"# 测试 {i}/{len(test_cases)}")
        print(f"{'#' * 70}")

        if test_github_analysis(test_case["url"], test_case["description"]):
            passed += 1
        else:
            failed += 1

    # 总结
    print("\n\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总计: {len(test_cases)} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {passed / len(test_cases) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
