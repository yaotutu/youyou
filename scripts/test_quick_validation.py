"""快速验证测试 - 核心功能"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')


def test_imports():
    """测试 1: 验证导入是否正常"""
    print("=" * 60)
    print("测试 1: 验证导入")
    print("=" * 60)

    try:
        # 测试通用工具导入
        from tools.github import GitHubAnalyzer
        from tools.storage import NoteStorage, NoteType, NoteUtils
        print("✅ 通用工具导入成功")

        # 测试 Agent 导入
        from agents.note_agent.agent import note_agent
        print("✅ NoteAgent 导入成功")

        # 测试配置
        from config import Config
        config = Config()
        print("✅ Config 加载成功")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_instantiation():
    """测试 2: 验证工具实例化"""
    print("\n" + "=" * 60)
    print("测试 2: 验证工具实例化")
    print("=" * 60)

    try:
        from config import Config
        from tools.github import GitHubAnalyzer
        from tools.storage import NoteStorage, NoteUtils

        config = Config()

        # 实例化工具
        analyzer = GitHubAnalyzer(config)
        print("✅ GitHubAnalyzer 实例化成功")

        storage = NoteStorage(config)
        print("✅ NoteStorage 实例化成功")

        utils = NoteUtils(config)
        print("✅ NoteUtils 实例化成功")

        return True
    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_parsing():
    """测试 3: 验证 URL 解析功能"""
    print("\n" + "=" * 60)
    print("测试 3: 验证 URL 解析功能")
    print("=" * 60)

    try:
        from config import Config
        from tools.github import GitHubAnalyzer

        config = Config()
        analyzer = GitHubAnalyzer(config)

        test_urls = [
            "https://github.com/fastapi/fastapi",
            "https://github.com/fastapi/fastapi/tree/main/docs",
            "fastapi/fastapi",
        ]

        for url in test_urls:
            result = analyzer._extract_repo_info(url)
            if result and result['owner'] == 'fastapi' and result['repo'] == 'fastapi':
                print(f"  ✅ {url}")
            else:
                print(f"  ❌ {url} - 解析失败")
                return False

        print("✅ URL 解析功能正常")
        return True
    except Exception as e:
        print(f"❌ URL 解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_note_query():
    """测试 4: 验证笔记查询"""
    print("\n" + "=" * 60)
    print("测试 4: 验证笔记查询（简单查询）")
    print("=" * 60)

    try:
        from agents.note_agent.agent import note_agent

        # 简单查询测试
        response = note_agent.invoke("我的笔记本里有多少笔记？")

        if response and len(response) > 0:
            print(f"✅ 查询成功，响应长度: {len(response)} 字符")
            print(f"响应预览: {response[:200]}...")
            return True
        else:
            print("❌ 查询返回空响应")
            return False

    except Exception as e:
        print(f"❌ 查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有快速验证测试"""
    print("\n" + "🚀 " + "=" * 56)
    print("   YouYou 快速验证测试")
    print("=" * 60 + "\n")

    tests = [
        ("导入测试", test_imports),
        ("实例化测试", test_tool_instantiation),
        ("URL 解析测试", test_url_parsing),
        ("笔记查询测试", test_note_query),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总计: {len(tests)} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {passed / len(tests) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 所有快速验证测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
