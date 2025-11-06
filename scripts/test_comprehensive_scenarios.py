"""综合场景测试 - 模拟真实用户使用"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from agents.note_agent.agent import note_agent
import time


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_scenario(scenario_name: str, query: str, expected_behavior: str):
    """测试一个场景"""
    print(f"📝 场景: {scenario_name}")
    print(f"🎯 查询: {query}")
    print(f"💡 期望行为: {expected_behavior}")
    print("-" * 80)

    try:
        start_time = time.time()
        response = note_agent.invoke(query)
        elapsed = time.time() - start_time

        print(f"\n✅ 响应 (耗时: {elapsed:.2f}s):")
        print("-" * 80)
        print(response[:600] if len(response) > 600 else response)
        if len(response) > 600:
            print("...(省略)")
        print("-" * 80)
        return True

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行综合测试场景"""
    print_section("YouYou 综合场景测试")

    scenarios = [
        # ========== 场景组 1: GitHub 项目管理 ==========
        {
            "name": "保存新项目（完整URL）",
            "query": "https://github.com/anthropics/anthropic-sdk-python",
            "expected": "识别为 GitHub URL，调用 analyze_github_project，保存项目信息"
        },
        {
            "name": "查询已保存项目",
            "query": "给我讲讲 FastAPI 这个项目",
            "expected": "搜索笔记本中的 FastAPI 内容，不分析新项目"
        },
        {
            "name": "列出所有 GitHub 项目",
            "query": "我收藏了哪些 GitHub 项目？",
            "expected": "列出所有 note_type=github_project 的笔记"
        },

        # ========== 场景组 2: 技术栈搜索 ==========
        {
            "name": "按技术栈搜索",
            "query": "搜索关于 Python 的项目",
            "expected": "搜索标签或内容包含 Python 的笔记"
        },
        {
            "name": "按多个关键词搜索",
            "query": "查找关于 Python 和 API 的内容",
            "expected": "混合搜索，找到相关笔记"
        },

        # ========== 场景组 3: 语义搜索 ==========
        {
            "name": "语义搜索 - 功能需求",
            "query": "我需要一个异步的 Web 框架",
            "expected": "通过语义理解找到 FastAPI 等异步框架"
        },
        {
            "name": "语义搜索 - 照片管理",
            "query": "有没有自托管的照片管理工具？",
            "expected": "找到 Immich 相关项目"
        },

        # ========== 场景组 4: 笔记管理 ==========
        {
            "name": "保存灵感笔记",
            "query": "记一下：Python 的异步编程可以用 asyncio 和 await 语法实现",
            "expected": "调用 save_note，保存为 inspiration 类型"
        },
        {
            "name": "搜索之前的灵感",
            "query": "我之前记录过关于异步编程的笔记吗？",
            "expected": "搜索笔记本中关于异步编程的内容"
        },

        # ========== 场景组 5: 边界测试 ==========
        {
            "name": "空查询",
            "query": "我的笔记本里有什么？",
            "expected": "列出所有笔记或统计信息"
        },
        {
            "name": "不存在的项目",
            "query": "给我讲讲 NonExistentProject12345",
            "expected": "搜索不到，提示用户没有相关笔记"
        },

        # ========== 场景组 6: 意图识别 ==========
        {
            "name": "模糊查询 - 项目名",
            "query": "immich 怎么样？",
            "expected": "搜索笔记本中的 Immich 内容，不分析新项目"
        },
        {
            "name": "URL 变体 - 简写",
            "query": "anthropics/anthropic-sdk-python",
            "expected": "识别为 GitHub 简写格式，分析项目"
        },
    ]

    passed = 0
    failed = 0

    for i, scenario in enumerate(scenarios, 1):
        print_section(f"场景 {i}/{len(scenarios)}")

        if test_scenario(
            scenario["name"],
            scenario["query"],
            scenario["expected"]
        ):
            passed += 1
        else:
            failed += 1

        # 暂停一下，避免 API 限流
        if i < len(scenarios):
            print("\n⏸  等待 2 秒...\n")
            time.sleep(2)

    # 总结
    print_section("测试总结")
    print(f"总计: {len(scenarios)} 个场景")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {passed / len(scenarios) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 所有场景测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个场景失败")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
