"""测试 GitHub URL 提取功能"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from config import Config
from agents.note_agent.github_analyzer import GitHubAnalyzer


def test_url_extraction():
    """测试各种 GitHub URL 的提取"""
    print("=" * 70)
    print("GitHub URL 提取功能测试")
    print("=" * 70)

    config = Config()
    analyzer = GitHubAnalyzer(config)

    # 测试用例
    test_cases = [
        # 基础格式
        {
            "url": "https://github.com/fastapi/fastapi",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "repo", "path": None}
        },
        # 子目录
        {
            "url": "https://github.com/fastapi/fastapi/tree/main/docs",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "directory", "path": "/tree/docs"}
        },
        # 文件
        {
            "url": "https://github.com/fastapi/fastapi/blob/main/README.md",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "file", "path": "/blob/README.md"}
        },
        # Issue
        {
            "url": "https://github.com/fastapi/fastapi/issues/123",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "issue", "path": "/issues/123"}
        },
        # PR
        {
            "url": "https://github.com/fastapi/fastapi/pull/456",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "pr", "path": "/pull/456"}
        },
        # 简写格式
        {
            "url": "fastapi/fastapi",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "repo", "path": None}
        },
        # 带 .git 后缀
        {
            "url": "https://github.com/fastapi/fastapi.git",
            "expected": {"owner": "fastapi", "repo": "fastapi", "type": "repo", "path": None}
        },
        # 复杂子目录
        {
            "url": "https://github.com/langchain-ai/langchain/tree/master/libs/langchain/langchain/agents",
            "expected": {"owner": "langchain-ai", "repo": "langchain", "type": "directory", "path": "/tree/libs/langchain/langchain/agents"}
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        url = test_case["url"]
        expected = test_case["expected"]

        print(f"\n测试 {i}: {url}")
        print("-" * 70)

        result = analyzer._extract_repo_info(url)

        if not result:
            print("❌ 提取失败：返回 None")
            failed += 1
            continue

        # 验证结果
        checks = {
            "owner": result.get("owner") == expected["owner"],
            "repo": result.get("repo") == expected["repo"],
            "type": result.get("resource_type") == expected["type"],
        }

        # 路径检查（模糊匹配，因为完整路径可能包含分支名）
        if expected["path"]:
            path_ok = result.get("path") and expected["path"].split("/")[-1] in result.get("path", "")
        else:
            path_ok = result.get("path") is None

        checks["path"] = path_ok

        all_passed = all(checks.values())

        if all_passed:
            print(f"✅ 通过")
            print(f"   Owner: {result['owner']}")
            print(f"   Repo: {result['repo']}")
            print(f"   Type: {result['resource_type']}")
            if result.get('path'):
                print(f"   Path: {result['path']}")
            passed += 1
        else:
            print(f"❌ 失败")
            print(f"   预期: {expected}")
            print(f"   实际: owner={result.get('owner')}, repo={result.get('repo')}, type={result.get('resource_type')}, path={result.get('path')}")
            for key, status in checks.items():
                if not status:
                    print(f"   ⚠️  {key} 不匹配")
            failed += 1

    # 总结
    print("\n" + "=" * 70)
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
    success = test_url_extraction()
    sys.exit(0 if success else 1)
