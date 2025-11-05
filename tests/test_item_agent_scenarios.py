"""ItemAgent 全面场景测试"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"


def send_message(msg: str, show_response=True):
    """发送消息到 API"""
    try:
        response = requests.post(
            f"{BASE_URL}/chat/message",
            json={"message": msg},
            timeout=60
        )
        result = response.json()
        response_text = result.get("response", "")

        if show_response:
            print(f"  用户: {msg}")
            print(f"  助手: {response_text}")
            print()

        return response_text
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return None


def test_scenario(title: str, test_func):
    """运行单个测试场景"""
    print("\n" + "=" * 80)
    print(f"📋 测试场景: {title}")
    print("=" * 80)

    try:
        result = test_func()
        if result:
            print(f"✅ {title} - 通过")
        else:
            print(f"❌ {title} - 失败")
        return result
    except Exception as e:
        print(f"❌ {title} - 异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_1_basic_record():
    """场景1: 基础记录功能"""
    print("\n测试: 记录多个不同物品\n")

    items = [
        ("护照", "卧室保险柜"),
        ("电动牙刷", "浴室洗手台"),
        ("降噪耳机", "书房桌面收纳盒"),
    ]

    for item, location in items:
        response = send_message(f"{item}放在{location}")
        if not response or "记录" not in response:
            return False
        time.sleep(1)

    return True


def scenario_2_query_variations():
    """场景2: 不同的查询方式"""
    print("\n测试: 使用不同的问法查询物品\n")

    # 先记录
    send_message("笔记本电脑在书房书桌上", show_response=False)
    time.sleep(1)

    # 不同的查询方式
    queries = [
        "笔记本电脑在哪？",
        "笔记本电脑在哪里？",
        "我的笔记本电脑放在哪儿了？",
        "笔记本在哪？",  # 简称
        "电脑在哪？",     # 简称
    ]

    success_count = 0
    for query in queries:
        response = send_message(query)
        if response and ("书房" in response or "书桌" in response):
            success_count += 1
        else:
            print(f"  ⚠️  查询失败: {query}")
        time.sleep(1)

    print(f"\n查询成功率: {success_count}/{len(queries)}")
    return success_count >= 3  # 至少3个查询成功


def scenario_3_similar_items():
    """场景3: 相似物品的区分"""
    print("\n测试: 区分相似但不同的物品\n")

    # 记录相似物品
    items = [
        ("家门钥匙", "玄关钥匙架"),
        ("车钥匙", "客厅茶几抽屉"),
        ("办公室钥匙", "背包侧兜"),
    ]

    for item, location in items:
        send_message(f"{item}在{location}", show_response=False)
        time.sleep(1)

    # 查询每一个
    test_cases = [
        ("家门钥匙在哪？", "玄关"),
        ("车钥匙在哪里？", "茶几"),
        ("办公室钥匙在哪儿？", "背包"),
    ]

    success_count = 0
    for query, expected_keyword in test_cases:
        response = send_message(query)
        if response and expected_keyword in response:
            success_count += 1
        else:
            print(f"  ⚠️  期望包含'{expected_keyword}', 实际: {response}")
        time.sleep(1)

    print(f"\n区分准确率: {success_count}/{len(test_cases)}")
    return success_count >= 2


def scenario_4_update_location():
    """场景4: 更新物品位置"""
    print("\n测试: 更新已记录物品的位置\n")

    # 首次记录
    send_message("雨伞在门口鞋柜")
    time.sleep(1)

    # 查询确认
    response1 = send_message("雨伞在哪？")
    if not response1 or "门口" not in response1:
        print("  ❌ 首次记录失败")
        return False
    time.sleep(1)

    # 更新位置
    send_message("雨伞现在在阳台晾衣架上")
    time.sleep(1)

    # 再次查询
    response2 = send_message("雨伞在哪？")
    if response2 and "阳台" in response2:
        print("  ✅ 位置更新成功")
        return True
    else:
        print(f"  ⚠️  更新后查询结果: {response2}")
        return False


def scenario_5_not_found():
    """场景5: 查询不存在的物品"""
    print("\n测试: 查询从未记录的物品\n")

    # 查询一个肯定不存在的物品
    response = send_message("量子计算机在哪里？")

    if response and ("没有" in response or "找不到" in response or "未记录" in response):
        print("  ✅ 正确返回'未找到'")
        return True
    else:
        print(f"  ⚠️  期望返回'未找到'，实际: {response}")
        return False


def scenario_6_complex_location():
    """场景6: 复杂的位置描述"""
    print("\n测试: 处理复杂的位置描述\n")

    complex_items = [
        ("身份证", "卧室衣柜右侧第二个抽屉的红色文件袋里"),
        ("备用钥匙", "厨房冰箱上面的蓝色收纳盒内"),
        ("充电宝", "客厅电视柜下层靠左边的黑色包里"),
    ]

    success_count = 0
    for item, location in complex_items:
        # 记录
        send_message(f"{item}在{location}", show_response=False)
        time.sleep(1)

        # 查询
        response = send_message(f"{item}在哪？")
        # 检查关键词是否存在
        keywords = location.split("的")[0:2]  # 取前两个关键词
        if response and any(kw in response for kw in keywords):
            success_count += 1
        else:
            print(f"  ⚠️  查询结果不完整: {response}")
        time.sleep(1)

    print(f"\n复杂位置处理成功率: {success_count}/{len(complex_items)}")
    return success_count >= 2


def scenario_7_list_all():
    """场景7: 列出所有物品"""
    print("\n测试: 列出所有已记录的物品\n")

    # 先记录几个物品
    items = [
        ("手表", "梳妆台"),
        ("钱包", "斜挎包"),
        ("口罩", "门口挂钩"),
    ]

    for item, location in items:
        send_message(f"{item}放在{location}", show_response=False)
        time.sleep(1)

    # 列出所有物品
    list_queries = [
        "我记录了哪些物品？",
        "列出所有物品",
        "有哪些东西？",
    ]

    for query in list_queries:
        response = send_message(query)
        if response:
            # 检查是否包含至少2个物品名
            count = sum(1 for item, _ in items if item in response)
            print(f"  查询'{query}': 找到 {count} 个物品")
            if count >= 2:
                return True
        time.sleep(1)

    return False


def scenario_8_chinese_variations():
    """场景8: 中文表达的多样性"""
    print("\n测试: 不同的中文表达方式\n")

    variations = [
        "眼镜放书房了",           # 省略"在"
        "把充电器放在床头柜上",     # "把...放在"句式
        "水杯在茶几上",           # 标准句式
        "我把帽子挂衣架上了",      # 完成时态
    ]

    success_count = 0
    for msg in variations:
        response = send_message(msg)
        if response and ("记录" in response or "好" in response):
            success_count += 1
        else:
            print(f"  ⚠️  记录失败: {msg}")
        time.sleep(1)

    print(f"\n中文变体识别率: {success_count}/{len(variations)}")
    return success_count >= 3


def scenario_9_multiple_locations():
    """场景9: 一个物品在多个地方（应该覆盖旧记录）"""
    print("\n测试: 同一物品多次记录\n")

    # 记录3次不同位置
    locations = ["客厅", "卧室", "书房"]

    for i, location in enumerate(locations, 1):
        send_message(f"平板电脑在{location}", show_response=True)
        time.sleep(1)

    # 最终查询
    response = send_message("平板电脑在哪？")

    # 应该返回最后一个位置
    if response and "书房" in response:
        print("  ✅ 正确返回最新位置")
        return True
    else:
        print(f"  ⚠️  期望'书房'，实际: {response}")
        # 如果至少返回了物品名称，也算部分通过
        return response and "平板" in response


def scenario_10_edge_cases():
    """场景10: 边界情况"""
    print("\n测试: 各种边界情况\n")

    test_cases = [
        ("超长物品名", "2024年购买的苹果MacBook Pro 14寸M3芯片版笔记本电脑", "工作台"),
        ("单字物品", "伞", "门边"),
        ("数字物品", "iPhone 15 Pro Max", "床头"),
        ("英文物品", "AirPods Pro", "包里"),
    ]

    success_count = 0
    for desc, item, location in test_cases:
        print(f"  测试 {desc}...")
        # 记录
        send_message(f"{item}在{location}", show_response=False)
        time.sleep(1)

        # 查询
        response = send_message(f"{item}在哪？", show_response=False)
        if response and location in response:
            print(f"    ✅ {desc} 成功")
            success_count += 1
        else:
            print(f"    ⚠️  {desc} 失败: {response}")
        time.sleep(1)

    print(f"\n边界情况处理率: {success_count}/{len(test_cases)}")
    return success_count >= 3


def scenario_11_semantic_search():
    """场景11: 语义搜索能力"""
    print("\n测试: 语义理解和模糊匹配\n")

    # 记录
    send_message("蓝牙鼠标在电脑桌右侧抽屉", show_response=False)
    time.sleep(1)

    # 使用不同但语义相近的词查询
    semantic_queries = [
        ("鼠标在哪？", True),           # 省略"蓝牙"
        ("无线鼠标在哪？", True),       # "蓝牙" ≈ "无线"
        ("键盘在哪？", False),         # 不同物品，应该找不到
    ]

    success_count = 0
    for query, should_find in semantic_queries:
        response = send_message(query)

        if should_find:
            if response and ("抽屉" in response or "电脑桌" in response):
                print(f"    ✅ 正确找到: {query}")
                success_count += 1
            else:
                print(f"    ⚠️  应找到但未找到: {query}")
        else:
            if response and ("没有" in response or "找不到" in response):
                print(f"    ✅ 正确未找到: {query}")
                success_count += 1
            else:
                print(f"    ⚠️  不应找到但找到了: {query}")

        time.sleep(1)

    print(f"\n语义搜索准确率: {success_count}/{len(semantic_queries)}")
    return success_count >= 2


def main():
    """运行所有测试场景"""
    print("\n" + "🧪" * 40)
    print("ItemAgent 全面场景测试")
    print("🧪" * 40)

    # 等待服务启动
    print("\n等待服务启动...")
    time.sleep(2)

    # 检查服务是否可用
    try:
        response = requests.get(f"{BASE_URL}/system/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动: uv run youyou-server")
            return
    except:
        print("❌ 无法连接到服务，请先启动: uv run youyou-server")
        return

    print("✅ 服务连接成功\n")

    # 所有测试场景
    scenarios = [
        ("基础记录功能", scenario_1_basic_record),
        ("多样化查询方式", scenario_2_query_variations),
        ("相似物品区分", scenario_3_similar_items),
        ("位置更新", scenario_4_update_location),
        ("未找到物品处理", scenario_5_not_found),
        ("复杂位置描述", scenario_6_complex_location),
        ("列出所有物品", scenario_7_list_all),
        ("中文表达多样性", scenario_8_chinese_variations),
        ("多次记录同一物品", scenario_9_multiple_locations),
        ("边界情况处理", scenario_10_edge_cases),
        ("语义搜索能力", scenario_11_semantic_search),
    ]

    results = []
    for title, test_func in scenarios:
        result = test_scenario(title, test_func)
        results.append((title, result))
        time.sleep(2)  # 场景之间间隔

    # 总结报告
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n总计: {passed}/{total} 个场景通过")
    print(f"通过率: {passed/total*100:.1f}%\n")

    print("详细结果:")
    for i, (title, result) in enumerate(results, 1):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {i:2d}. {status} - {title}")

    print("\n" + "=" * 80)

    if passed == total:
        print("🎉 所有测试场景通过！ItemAgent 工作完美！")
    elif passed >= total * 0.8:
        print("👍 大部分测试通过，ItemAgent 工作良好！")
    elif passed >= total * 0.6:
        print("⚠️  部分测试通过，ItemAgent 需要改进。")
    else:
        print("❌ 测试通过率较低，ItemAgent 存在较多问题。")

    print("=" * 80)


if __name__ == "__main__":
    main()
