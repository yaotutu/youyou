"""完整流程测试 - 通过 HTTP API"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"


def send_message(msg: str):
    """发送消息到 API"""
    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={"message": msg}
    )
    result = response.json()
    return result.get("response", "")


def test_complete_flow():
    """测试完整的记录-查询流程"""
    print("\n" + "=" * 60)
    print("测试: 完整的物品记录和查询流程")
    print("=" * 60)

    # 等待服务启动
    time.sleep(2)

    # 1. 记录几个物品
    print("\n--- 步骤 1: 记录物品 ---")

    response1 = send_message("雨伞放在客厅柜子里")
    print(f"记录雨伞: {response1}")

    time.sleep(1)

    response2 = send_message("充电器在书房抽屉")
    print(f"记录充电器: {response2}")

    time.sleep(1)

    # 2. 查询物品
    print("\n--- 步骤 2: 查询物品 ---")

    response3 = send_message("雨伞在哪？")
    print(f"查询雨伞: {response3}")

    time.sleep(1)

    response4 = send_message("充电器在哪里？")
    print(f"查询充电器: {response4}")

    # 3. 验证结果
    print("\n--- 步骤 3: 验证结果 ---")

    success = True
    if "客厅" not in response3 and "柜子" not in response3:
        print(f"❌ 雨伞位置错误: {response3}")
        success = False
    else:
        print(f"✅ 雨伞位置正确: {response3}")

    if "书房" not in response4 and "抽屉" not in response4:
        print(f"❌ 充电器位置错误: {response4}")
        success = False
    else:
        print(f"✅ 充电器位置正确: {response4}")

    # 4. 测试对话功能
    print("\n--- 步骤 4: 测试对话功能 ---")

    response5 = send_message("你好")
    print(f"对话测试: {response5}")

    if response5:
        print("✅ 对话功能正常")
    else:
        print("❌ 对话功能异常")
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return success


if __name__ == "__main__":
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请先启动服务: uv run youyou-server")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
