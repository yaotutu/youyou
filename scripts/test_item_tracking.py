"""物品追踪功能完整测试

测试场景:
1. 记录多个物品
2. 精确查询
3. 模糊查询
4. 别名查询
5. 更新位置
6. 列出所有物品
7. 记忆混淆验证
"""
from core.database import get_database
from config import config


def print_section(title):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_basic_operations():
    """测试 1: 基础操作 - 记录和查询"""
    print_section("测试 1: 基础操作")

    db = get_database()

    # 记录几个物品
    items = [
        ("钥匙", "客厅茶几"),
        ("充电器", "卧室床头柜"),
        ("耳机", "书房抽屉"),
        ("雨伞", "玄关鞋柜"),
        ("口罩", "玄关挂钩"),
    ]

    print("\n📝 记录物品:")
    for item, location in items:
        result = db.remember_item(item, location, config.USER_ID)
        status = "✅" if result["status"] == "success" else "❌"
        print(f"{status} {item} -> {location}")

    # 精确查询
    print("\n🔍 精确查询:")
    queries = ["钥匙", "充电器", "耳机"]
    for query in queries:
        result = db.query_item(query, config.USER_ID)
        if result["status"] == "success":
            print(f"✅ {query} 在 {result['location']}")
        else:
            print(f"❌ 未找到 {query}")


def test_fuzzy_search():
    """测试 2: 模糊搜索"""
    print_section("测试 2: 模糊搜索")

    db = get_database()

    # 记录物品
    db.remember_item("苹果手机", "客厅沙发", config.USER_ID)
    db.remember_item("iPad平板", "书房桌面", config.USER_ID)
    db.remember_item("MacBook笔记本", "卧室床上", config.USER_ID)

    print("\n🔍 模糊查询:")
    queries = ["手机", "平板", "笔记本", "苹果"]

    for query in queries:
        result = db.query_item(query, config.USER_ID)
        if result["status"] == "success":
            match_type = result.get("match_type", "unknown")
            print(f"✅ '{query}' 找到: {result['item']} 在 {result['location']} (匹配方式: {match_type})")
        else:
            print(f"❌ '{query}' 未找到")


def test_location_update():
    """测试 3: 位置更新"""
    print_section("测试 3: 位置更新")

    db = get_database()

    # 初始记录
    print("\n📝 初始记录:")
    result = db.remember_item("水杯", "厨房", config.USER_ID)
    print(f"✅ 水杯 -> 厨房")

    # 查询初始位置
    result = db.query_item("水杯", config.USER_ID)
    print(f"🔍 当前位置: {result['location']}")

    # 更新位置
    print("\n📝 更新位置:")
    result = db.remember_item("水杯", "书房", config.USER_ID)
    action = result.get("action", "unknown")
    print(f"✅ 水杯 -> 书房 (操作: {action})")

    # 查询新位置
    result = db.query_item("水杯", config.USER_ID)
    print(f"🔍 新位置: {result['location']}")

    # 再次记录相同位置(不应更新)
    print("\n📝 重复记录相同位置:")
    result = db.remember_item("水杯", "书房", config.USER_ID)
    action = result.get("action", "unknown")
    print(f"✅ 水杯 -> 书房 (操作: {action})")


def test_list_items():
    """测试 4: 列出所有物品"""
    print_section("测试 4: 列出所有物品")

    db = get_database()

    result = db.list_all_items(config.USER_ID)

    if result["status"] == "success":
        count = result["count"]
        print(f"\n📋 共有 {count} 个物品:")

        for item in result["items"]:
            print(f"  • {item['item']:15} -> {item['location']}")
    else:
        print("❌ 获取物品列表失败")


def test_memory_confusion():
    """测试 5: 记忆混淆验证 (核心 Bug 修复测试)"""
    print_section("测试 5: 记忆混淆验证")

    db = get_database()

    # 记录一些不相关的物品
    print("\n📝 记录物品:")
    items = [
        ("梳妆台", "卧室"),
        ("电视机", "客厅"),
        ("洗衣机", "阳台"),
    ]

    for item, location in items:
        db.remember_item(item, location, config.USER_ID)
        print(f"✅ {item} -> {location}")

    # 查询不存在的物品
    print("\n🔍 查询不存在的物品:")
    non_existent = ["时光机", "传送门", "魔法棒", "飞行扫帚"]

    for query in non_existent:
        result = db.query_item(query, config.USER_ID)
        if result["status"] == "not_found":
            print(f"✅ '{query}' 正确返回 not_found (没有混淆)")
        elif result["status"] == "success":
            print(f"❌ '{query}' 错误返回: {result['item']} (发生混淆!)")
        else:
            print(f"⚠️  '{query}' 返回未知状态: {result.get('status')}")


def test_alias_matching():
    """测试 6: 别名匹配"""
    print_section("测试 6: 别名匹配")

    db = get_database()

    # 记录带多个别名的物品
    print("\n📝 记录物品:")
    db.remember_item("电视遥控器", "客厅茶几", config.USER_ID)
    print("✅ 电视遥控器 -> 客厅茶几")

    # 尝试不同的查询方式
    print("\n🔍 别名查询:")
    queries = ["遥控器", "电视遥控", "遥控", "TV遥控器"]

    for query in queries:
        result = db.query_item(query, config.USER_ID)
        if result["status"] == "success":
            match_type = result.get("match_type", "unknown")
            print(f"✅ '{query}' 找到: {result['item']} (匹配方式: {match_type})")
        else:
            print(f"❌ '{query}' 未找到")


def test_chinese_normalization():
    """测试 7: 中文规范化"""
    print_section("测试 7: 中文规范化")

    db = get_database()

    # 记录带空格和标点的物品
    print("\n📝 记录物品 (带空格/标点):")
    db.remember_item("笔记本 电脑", "书房", config.USER_ID)
    db.remember_item("手机充电器", "卧室", config.USER_ID)
    print("✅ '笔记本 电脑' -> 书房")
    print("✅ '手机充电器' -> 卧室")

    # 使用不同格式查询
    print("\n🔍 规范化查询:")
    queries = [
        ("笔记本电脑", "书房"),  # 无空格
        ("手机 充电器", "卧室"),  # 带空格
    ]

    for query, expected_location in queries:
        result = db.query_item(query, config.USER_ID)
        if result["status"] == "success":
            match = "✅" if result["location"] == expected_location else "⚠️"
            print(f"{match} '{query}' -> {result['location']}")
        else:
            print(f"❌ '{query}' 未找到")


def test_performance():
    """测试 8: 性能测试"""
    print_section("测试 8: 性能测试")

    import time
    db = get_database()

    # 批量记录
    print("\n📝 批量记录 50 个物品:")
    start = time.time()

    for i in range(50):
        db.remember_item(f"物品{i}", f"位置{i%10}", config.USER_ID)

    elapsed = time.time() - start
    print(f"✅ 完成, 耗时: {elapsed:.2f}s ({50/elapsed:.1f} items/s)")

    # 批量查询
    print("\n🔍 批量查询 50 个物品:")
    start = time.time()

    success_count = 0
    for i in range(50):
        result = db.query_item(f"物品{i}", config.USER_ID)
        if result["status"] == "success":
            success_count += 1

    elapsed = time.time() - start
    print(f"✅ 完成, 耗时: {elapsed:.2f}s ({50/elapsed:.1f} queries/s)")
    print(f"   成功查询: {success_count}/50")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*20 + "物品追踪功能测试")
    print("="*70)

    try:
        test_basic_operations()
        test_fuzzy_search()
        test_location_update()
        test_list_items()
        test_memory_confusion()
        test_alias_matching()
        test_chinese_normalization()
        test_performance()

        print("\n" + "="*70)
        print("🎉 所有测试完成!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
