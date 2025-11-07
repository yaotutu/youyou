"""测试 CalendarAgent 功能

注意：此测试需要配置 CalDAV 才能运行
请在 .env 文件中配置：
- CALDAV_URL
- CALDAV_USERNAME
- CALDAV_PASSWORD
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agents.calendar_agent import calendar_agent
from config import config


def check_caldav_config():
    """检查 CalDAV 配置"""
    print("=" * 60)
    print("检查 CalDAV 配置")
    print("=" * 60)

    if not config.CALDAV_URL:
        print("❌ 未配置 CALDAV_URL")
        print("\n请在 .env 文件中配置：")
        print("  CALDAV_URL=https://caldav.icloud.com")
        print("  CALDAV_USERNAME=your_email@example.com")
        print("  CALDAV_PASSWORD=your_app_specific_password")
        return False

    print(f"✅ CALDAV_URL: {config.CALDAV_URL}")
    print(f"✅ CALDAV_USERNAME: {config.CALDAV_USERNAME}")
    print(f"✅ CALDAV_PASSWORD: {'*' * 10 if config.CALDAV_PASSWORD else '未设置'}")
    print(f"✅ CALDAV_CALENDAR_NAME: {config.CALDAV_CALENDAR_NAME or '默认'}")
    print(f"✅ 默认提前提醒: {config.CALDAV_DEFAULT_REMINDER_MINUTES} 分钟")
    return True


def test_add_reminder():
    """测试添加提醒"""
    print("\n" + "=" * 60)
    print("测试 1：添加简单提醒")
    print("=" * 60)

    result = calendar_agent.invoke("明天上午八点提醒我拿充电器")
    print(result)


def test_list_reminders():
    """测试查询提醒"""
    print("\n" + "=" * 60)
    print("测试 2：查询今天的提醒")
    print("=" * 60)

    result = calendar_agent.invoke("我今天有什么提醒？")
    print(result)


def test_list_week_reminders():
    """测试查询本周提醒"""
    print("\n" + "=" * 60)
    print("测试 3：查询本周的提醒")
    print("=" * 60)

    result = calendar_agent.invoke("列出本周的提醒")
    print(result)


def test_complex_time():
    """测试复杂时间表达"""
    print("\n" + "=" * 60)
    print("测试 4：复杂时间表达（提前半小时提醒）")
    print("=" * 60)

    result = calendar_agent.invoke("下周一下午三点开会，提前半小时提醒我")
    print(result)


def test_multiple_reminders():
    """测试添加多个提醒"""
    print("\n" + "=" * 60)
    print("测试 5：添加多个提醒")
    print("=" * 60)

    test_cases = [
        "明天中午12点提醒我吃药",
        "后天上午10点提醒我开会",
        "下周五晚上8点提醒我聚餐"
    ]

    for user_input in test_cases:
        print(f"\n输入: {user_input}")
        result = calendar_agent.invoke(user_input)
        print(result)


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("CalendarAgent 功能测试")
    print("=" * 60)

    # 1. 检查配置
    if not check_caldav_config():
        print("\n⚠️ 请先配置 CalDAV 再运行测试")
        return

    try:
        # 2. 测试添加提醒
        test_add_reminder()

        # 3. 测试查询提醒
        test_list_reminders()

        # 4. 测试查询本周提醒
        test_list_week_reminders()

        # 5. 测试复杂时间
        test_complex_time()

        # 6. 测试添加多个提醒
        # test_multiple_reminders()  # 取消注释以测试

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
