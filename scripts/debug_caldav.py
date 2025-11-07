"""调试 CalDAV 连接问题"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from config import config
import caldav


def test_with_debug():
    """详细调试连接过程"""
    print("=" * 60)
    print("CalDAV 详细调试")
    print("=" * 60)

    print(f"\n配置信息:")
    print(f"  URL: {config.CALDAV_URL}")
    print(f"  Username: {config.CALDAV_USERNAME}")
    print(f"  Password: {'*' * 10}{config.CALDAV_PASSWORD[-4:]}")

    try:
        print("\n步骤 1: 创建 DAVClient...")
        client = caldav.DAVClient(
            url=config.CALDAV_URL,
            username=config.CALDAV_USERNAME,
            password=config.CALDAV_PASSWORD
        )
        print("✅ DAVClient 创建成功")

        print("\n步骤 2: 获取 Principal...")
        try:
            principal = client.principal()
            print(f"✅ Principal 获取成功")
            print(f"   Principal URL: {principal.url if hasattr(principal, 'url') else 'N/A'}")
        except Exception as e:
            print(f"❌ Principal 获取失败: {e}")
            print(f"\n尝试手动构建 Principal URL...")

            # 尝试不同的 Principal URL 模式
            possible_urls = [
                f"{config.CALDAV_URL}principals/{config.CALDAV_USERNAME}/",
                f"{config.CALDAV_URL}principals/users/{config.CALDAV_USERNAME}/",
                f"{config.CALDAV_URL}{config.CALDAV_USERNAME}/",
                f"{config.CALDAV_URL}CalDAV/{config.CALDAV_USERNAME}/",
            ]

            for url in possible_urls:
                print(f"\n尝试: {url}")
                try:
                    from caldav.objects import Principal as PrincipalClass
                    principal = PrincipalClass(client=client, url=url)
                    calendars = principal.calendars()
                    print(f"✅ 成功！找到 {len(calendars)} 个日历")
                    return principal
                except Exception as e2:
                    print(f"   失败: {e2}")

            print("\n❌ 所有尝试都失败了")
            return None

        print("\n步骤 3: 获取日历列表...")
        calendars = principal.calendars()
        print(f"✅ 找到 {len(calendars)} 个日历")

        for i, cal in enumerate(calendars, 1):
            print(f"\n日历 {i}:")
            print(f"  名称: {cal.name}")
            try:
                print(f"  URL: {cal.url}")
            except:
                pass

        return principal

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_with_debug()
