"""测试 CalDAV 自动发现功能"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from config import config
import caldav


def test_auto_discover():
    """使用自动发现功能"""
    print("=" * 60)
    print("CalDAV 自动发现测试")
    print("=" * 60)

    urls_to_try = [
        # QQ 邮箱可能的基础 URL
        "https://caldav.qq.com",
        "https://dav.qq.com",
        "https://caldav.qq.com/",
        "https://dav.qq.com/",
        # 带用户名的完整路径
        f"https://caldav.qq.com/{config.CALDAV_USERNAME}",
        f"https://dav.qq.com/{config.CALDAV_USERNAME}",
        # CalDAV 标准路径
        f"https://caldav.qq.com/CalDAV/{config.CALDAV_USERNAME}",
        f"https://dav.qq.com/CalDAV/{config.CALDAV_USERNAME}",
    ]

    for url in urls_to_try:
        print(f"\n尝试 URL: {url}")
        print("-" * 60)

        try:
            # 使用 caldav 的自动发现
            with caldav.DAVClient(
                url=url,
                username=config.CALDAV_USERNAME,
                password=config.CALDAV_PASSWORD
            ) as client:
                print("  ✓ 客户端创建成功")

                try:
                    principal = client.principal()
                    print(f"  ✓ Principal 获取成功")

                    calendars = principal.calendars()
                    print(f"  ✓ 找到 {len(calendars)} 个日历")

                    if calendars:
                        print("\n  🎉 成功！正确的 URL 是:")
                        print(f"     {url}")
                        print("\n  日历列表:")
                        for i, cal in enumerate(calendars, 1):
                            print(f"    {i}. {cal.name}")

                        print(f"\n  请在 .env 文件中设置:")
                        print(f"    CALDAV_URL={url}")
                        return url

                except Exception as e:
                    print(f"  ✗ 获取日历失败: {e}")

        except Exception as e:
            print(f"  ✗ 连接失败: {e}")

    print("\n" + "=" * 60)
    print("❌ 未找到可用的 URL")
    print("=" * 60)
    print("\n建议:")
    print("1. 检查你在 Mac 日历中配置的服务器地址")
    print("2. 确认已在 QQ 邮箱设置中开启 CalDAV 服务")
    print("3. 确认使用的是授权码（不是密码）")
    return None


if __name__ == "__main__":
    test_auto_discover()
