"""测试关键词路由器"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.keyword_router import KeywordRouter


def print_result(message: str, result):
    """打印路由结果"""
    print(f"\n{'='*80}")
    print(f"📝 消息: {message}")
    print(f"✓ 匹配: {'是' if result.matched else '否'}")
    if result.matched:
        print(f"🎯 目标 Agent: {result.target_agent}")
        print(f"📌 匹配的关键词: {', '.join(result.matched_keywords)}")
    print(f"{'='*80}")


def test_calendar_keywords():
    """测试日历关键词匹配"""
    print("\n" + "🔥"*40)
    print("测试 Calendar Agent 关键词路由")
    print("🔥"*40)

    # 应该匹配到 calendar_agent 的测试用例
    positive_cases = [
        # 动作关键词
        "晚上八点提醒我打卡",
        "明天上午提醒我拿充电器",
        "记得明天9点开会",
        "别忘了下周五交报告",
        "不要忘记今晚打卡",
        # 时间表达式
        "明天8点有安排吗",
        "今天下午开会",
        "下周三下午2点",
        "后天上午10点半",
        # 标记
        "#提醒 明天开会",
        "#calendar 今天日程",
        "/remind 打卡",
        # 组合
        "明天",
        "今天提醒",
        "8点打卡",
        "上午会议",
        "周一开会",
        "星期五日程",
        "12月25日圣诞节",
        "14:30分开会",
    ]

    print("\n✅ 应该匹配到 calendar_agent 的用例:")
    passed = 0
    failed = 0

    for msg in positive_cases:
        result = KeywordRouter.match(msg)
        if result.matched and result.target_agent == "calendar_agent":
            print(f"  ✓ '{msg}' → {result.target_agent} ({', '.join(result.matched_keywords)})")
            passed += 1
        else:
            print(f"  ✗ '{msg}' → {'未匹配' if not result.matched else result.target_agent}")
            failed += 1

    # 不应该匹配的测试用例
    negative_cases = [
        "你好",
        "今天天气怎么样",
        "钥匙在哪里",
        "我的护照放在书桌",
        "#note 测试笔记",
        "https://github.com/user/repo",
        "帮我写个代码",
    ]

    print("\n❌ 不应该匹配的用例:")
    for msg in negative_cases:
        result = KeywordRouter.match(msg)
        if not result.matched:
            print(f"  ✓ '{msg}' → 未匹配 (正确)")
            passed += 1
        else:
            print(f"  ✗ '{msg}' → {result.target_agent} (应该不匹配！)")
            failed += 1

    print(f"\n📊 测试结果: 通过 {passed}/{passed+failed} 项")
    return passed, failed


def test_specific_cases():
    """测试特定场景"""
    print("\n" + "🎯"*40)
    print("测试具体场景")
    print("🎯"*40)

    test_cases = [
        ("晚上八点提醒我打卡", True, "calendar_agent"),
        ("明天上午8点提醒我拿充电器", True, "calendar_agent"),
        ("我今天有什么提醒", True, "calendar_agent"),
        ("列出我的日程", True, "calendar_agent"),
        ("今天天气怎么样", False, None),
        ("钥匙在哪里", False, None),
    ]

    print("\n详细测试结果:")
    results = KeywordRouter.test(test_cases)

    for detail in results['details']:
        status = "✓" if detail['passed'] else "✗"
        print(f"\n{status} '{detail['message']}'")
        print(f"  预期: matched={detail['expected']['matched']}, agent={detail['expected']['agent']}")
        print(f"  实际: matched={detail['actual']['matched']}, agent={detail['actual']['agent']}")
        if detail['keywords']:
            print(f"  匹配关键词: {', '.join(detail['keywords'])}")

    print(f"\n📊 测试统计:")
    print(f"  总数: {results['total']}")
    print(f"  通过: {results['passed']}")
    print(f"  失败: {results['failed']}")
    print(f"  成功率: {results['passed']/results['total']*100:.1f}%")


def interactive_test():
    """交互式测试"""
    print("\n" + "💬"*40)
    print("交互式测试模式")
    print("💬"*40)
    print("输入消息测试关键词路由 (输入 'q' 退出)")

    while True:
        try:
            message = input("\n📝 输入消息: ").strip()
            if message.lower() == 'q':
                break

            if not message:
                continue

            result = KeywordRouter.match(message)
            print_result(message, result)

        except KeyboardInterrupt:
            print("\n\n👋 测试结束")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


def main():
    """主函数"""
    print("="*80)
    print("🧪 关键词路由器测试")
    print("="*80)

    # 1. 测试日历关键词
    passed1, failed1 = test_calendar_keywords()

    # 2. 测试特定场景
    test_specific_cases()

    # 3. 交互式测试
    print("\n")
    choice = input("是否进入交互式测试? (y/n): ").strip().lower()
    if choice == 'y':
        interactive_test()

    print("\n" + "="*80)
    print(f"🎉 测试完成！")
    print("="*80)


if __name__ == "__main__":
    main()
