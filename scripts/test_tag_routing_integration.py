"""测试标记路由与服务端集成"""
import requests
import time
import json


BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_api(message: str, description: str):
    """测试 API 请求"""
    print("\n" + "=" * 60)
    print(f"测试：{description}")
    print("=" * 60)
    print(f"输入消息: {message}")
    print("-" * 60)

    try:
        response = requests.post(
            f"{BASE_URL}/chat/message",
            json={"message": message},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            print(f"✅ 响应成功")
            print(f"响应内容（前500字）:\n{response_text[:500]}")
            if len(response_text) > 500:
                print("...")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("请先启动服务器: uv run youyou-server")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("🚀 开始测试标记路由集成...")
    print(f"API 地址: {BASE_URL}")

    # 检查服务器是否运行
    print("\n检查服务器状态...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/api/v1/system/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print("⚠️  服务器响应异常")
    except:
        print("❌ 服务器未启动，请先运行: uv run youyou-server")
        return

    # 测试用例
    test_cases = [
        # 测试 1：使用 #note 标记
        {
            "message": "#note Python 装饰器可以实现缓存、日志记录、权限验证等功能，非常强大。",
            "description": "使用 #note 标记保存笔记（英文标记）"
        },

        # 测试 2：使用中文标记
        {
            "message": "#笔记 Rust 的所有权系统可以在编译时防止数据竞争，保证内存安全。",
            "description": "使用 #笔记 标记保存笔记（中文标记）"
        },

        # 测试 3：使用斜杠格式
        {
            "message": "/note 学习了 React Hooks 的使用方法，特别是 useState 和 useEffect。",
            "description": "使用 /note 标记保存笔记（斜杠格式）"
        },

        # 测试 4：GitHub URL 自动识别
        {
            "message": "https://github.com/fastapi/fastapi",
            "description": "发送 GitHub URL（自动识别）"
        },

        # 测试 5：搜索笔记
        {
            "message": "搜索关于 Python 的笔记",
            "description": "搜索笔记（走 Supervisor 路由）"
        },

        # 测试 6：列出笔记
        {
            "message": "列出我的所有笔记",
            "description": "列出笔记（走 Supervisor 路由）"
        },

        # 测试 7：物品记录（不应该被标记路由）
        {
            "message": "钥匙在桌上",
            "description": "记录物品位置（走 Supervisor → ItemAgent）"
        },

        # 测试 8：普通对话（不应该被标记路由）
        {
            "message": "你好",
            "description": "普通对话（走 Supervisor → ChatAgent）"
        },
    ]

    success_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{total_count}]")
        if test_api(test_case["message"], test_case["description"]):
            success_count += 1

        # 测试间隔，避免请求过快
        if i < total_count:
            print("\n等待 2 秒...")
            time.sleep(2)

    # 总结
    print("\n" + "=" * 60)
    print("测试完成总结")
    print("=" * 60)
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count / total_count * 100:.1f}%")

    if success_count == total_count:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")


if __name__ == "__main__":
    main()
