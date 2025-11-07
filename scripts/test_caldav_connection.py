"""测试 CalDAV 连接

验证 CalDAV 配置是否正确，测试基本的连接和操作
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from config import config


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_config():
    """测试配置是否完整"""
    print_section("1. 检查配置")

    config_items = [
        ("CALDAV_URL", config.CALDAV_URL),
        ("CALDAV_USERNAME", config.CALDAV_USERNAME),
        ("CALDAV_PASSWORD", config.CALDAV_PASSWORD),
        ("CALDAV_CALENDAR_NAME", config.CALDAV_CALENDAR_NAME or "默认"),
        ("CALDAV_DEFAULT_REMINDER_MINUTES", config.CALDAV_DEFAULT_REMINDER_MINUTES),
    ]

    all_configured = True
    for name, value in config_items:
        if name == "CALDAV_PASSWORD":
            display_value = "*" * 10 + value[-4:] if value else "❌ 未设置"
        else:
            display_value = value if value else "❌ 未设置"

        status = "✅" if value else "❌"
        print(f"{status} {name}: {display_value}")

        if not value and name != "CALDAV_CALENDAR_NAME":
            all_configured = False

    if not all_configured:
        print("\n❌ 配置不完整！请在 .env 文件中配置缺失的项目。")
        return False

    print("\n✅ 配置完整")
    return True


def test_connection():
    """测试 CalDAV 连接"""
    print_section("2. 测试连接")

    try:
        import caldav

        print("正在连接到 CalDAV 服务器...")
        client = caldav.DAVClient(
            url=config.CALDAV_URL,
            username=config.CALDAV_USERNAME,
            password=config.CALDAV_PASSWORD
        )

        print("✅ CalDAV 客户端创建成功")

        # 获取 Principal
        print("正在获取 Principal...")
        principal = client.principal()
        print(f"✅ Principal 获取成功: {principal}")

        return client, principal

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        print("\n可能的原因：")
        print("1. CALDAV_URL 不正确")
        print("2. 用户名或密码错误")
        print("3. 网络连接问题")
        print("4. 需要使用 App 专用密码（iCloud、Google）")
        return None, None


def test_list_calendars(principal):
    """测试列出日历"""
    print_section("3. 列出所有日历")

    try:
        calendars = principal.calendars()

        if not calendars:
            print("⚠️ 未找到任何日历")
            return None

        print(f"✅ 找到 {len(calendars)} 个日历：\n")

        for i, cal in enumerate(calendars, 1):
            print(f"{i}. {cal.name}")
            try:
                print(f"   URL: {cal.url}")
            except:
                pass

        return calendars

    except Exception as e:
        print(f"❌ 列出日历失败: {str(e)}")
        return None


def test_create_event(calendars):
    """测试创建事件"""
    print_section("4. 测试创建事件")

    if not calendars:
        print("❌ 没有可用的日历")
        return None

    try:
        from icalendar import Calendar as iCal, Event, Alarm
        import uuid

        # 使用第一个日历
        calendar = calendars[0]
        print(f"使用日历: {calendar.name}")

        # 创建测试事件
        event = Event()
        event_uid = str(uuid.uuid4())

        now = datetime.now()
        start_time = now + timedelta(hours=1)  # 1小时后
        end_time = start_time + timedelta(minutes=30)

        event.add('uid', event_uid)
        event.add('summary', '【测试】CalDAV 连接测试')
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('dtstamp', now)
        event.add('description', f'这是一个测试事件，创建于 {now.strftime("%Y-%m-%d %H:%M:%S")}')

        # 添加提醒
        alarm = Alarm()
        alarm.add('ACTION', 'DISPLAY')
        alarm.add('DESCRIPTION', '【测试】CalDAV 连接测试')
        alarm.add('TRIGGER', timedelta(minutes=-10))
        event.add_component(alarm)

        # 创建日历容器
        cal = iCal()
        cal.add_component(event)

        # 保存事件
        print(f"正在创建事件...")
        print(f"  标题: 【测试】CalDAV 连接测试")
        print(f"  时间: {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  提醒: 提前 10 分钟")

        calendar.save_event(cal.to_ical())

        print(f"✅ 事件创建成功！")
        print(f"   事件 ID: {event_uid}")

        return event_uid

    except Exception as e:
        print(f"❌ 创建事件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_list_events(calendars):
    """测试列出事件"""
    print_section("5. 列出即将到来的事件")

    if not calendars:
        print("❌ 没有可用的日历")
        return

    try:
        calendar = calendars[0]
        now = datetime.now()
        end_date = now + timedelta(days=7)

        print(f"查询范围: {now.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")

        events = calendar.date_search(
            start=now,
            end=end_date,
            expand=True
        )

        events_list = list(events)

        if not events_list:
            print("📭 未来 7 天内没有事件")
            return

        print(f"✅ 找到 {len(events_list)} 个事件：\n")

        for i, event in enumerate(events_list, 1):
            try:
                ical_event = event.icalendar_component
                summary = str(ical_event.get('summary', '无标题'))
                dtstart = ical_event.get('dtstart')
                start_time = dtstart.dt if dtstart else '未知'

                print(f"{i}. {summary}")
                print(f"   时间: {start_time}")
                print(f"   UID: {ical_event.get('uid', '无')}")
                print()
            except Exception as e:
                print(f"{i}. [解析失败: {e}]")

    except Exception as e:
        print(f"❌ 列出事件失败: {str(e)}")


def test_delete_event(calendars, event_uid):
    """测试删除事件"""
    print_section("6. 删除测试事件")

    if not event_uid:
        print("⚠️ 没有要删除的事件 ID")
        return

    try:
        calendar = calendars[0]

        print(f"正在查找事件 ID: {event_uid}")
        events = calendar.events()

        for event in events:
            ical = event.icalendar_component
            if str(ical.get('uid', '')) == event_uid:
                print("找到测试事件，正在删除...")
                event.delete()
                print("✅ 测试事件已删除")
                return

        print("⚠️ 未找到测试事件（可能已被手动删除）")

    except Exception as e:
        print(f"❌ 删除失败: {str(e)}")


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("CalDAV 连接测试")
    print("=" * 60)

    # 1. 检查配置
    if not test_config():
        return

    # 2. 测试连接
    client, principal = test_connection()
    if not client or not principal:
        return

    # 3. 列出日历
    calendars = test_list_calendars(principal)
    if not calendars:
        return

    # 4. 创建测试事件
    event_uid = test_create_event(calendars)

    # 5. 列出事件
    test_list_events(calendars)

    # 6. 清理：删除测试事件
    if event_uid:
        print("\n是否删除测试事件？(y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                test_delete_event(calendars, event_uid)
            else:
                print("⚠️ 测试事件未删除，请手动清理")
        except KeyboardInterrupt:
            print("\n⚠️ 已跳过删除")

    # 关闭连接
    try:
        client.close()
        print("\n✅ 连接已关闭")
    except:
        pass

    print("\n" + "=" * 60)
    print("✅ CalDAV 测试完成！")
    print("=" * 60)
    print("\n如果所有测试都通过，说明 CalDAV 配置正确。")
    print("现在可以使用 CalendarAgent 添加真实的提醒了！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
