"""测试所有修复效果

测试内容:
1. 记忆混淆 Bug 修复 - 验证物品名称匹配
2. 线程安全单例 - 多线程并发访问
3. 消息提取逻辑 - 验证 BaseAgent 方法
4. 目录结构简化 - 验证导入路径
"""
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_import_structure():
    """测试 1: 验证目录结构简化后导入正常"""
    print("\n" + "="*60)
    print("测试 1: 验证目录结构 (tools/ 已合并)")
    print("="*60)

    try:
        # 应该失败 - tools/ 已删除
        try:
            from youyou.tools.item_tools import remember_item_location
            print("❌ tools/ 目录仍然存在")
            return False
        except ImportError:
            print("✅ tools/ 目录已删除")

        # 应该成功 - 从 item_agent 导入
        from youyou.agents.item_agent.tools import (
            remember_item_location,
            query_item_location,
            list_all_items
        )
        print("✅ 可以从 item_agent.tools 导入工具")

        return True

    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_agent_method():
    """测试 2: 验证 BaseAgent 消息提取方法"""
    print("\n" + "="*60)
    print("测试 2: 验证 BaseAgent 消息提取方法")
    print("="*60)

    try:
        from youyou.core.agent_base import BaseAgent

        # 测试提取方法存在
        if not hasattr(BaseAgent, '_extract_response_from_result'):
            print("❌ BaseAgent 缺少 _extract_response_from_result 方法")
            return False

        print("✅ BaseAgent._extract_response_from_result 方法存在")

        # 测试方法功能
        test_data = {
            "messages": [
                {"content": "test message"}
            ]
        }

        result = BaseAgent._extract_response_from_result(test_data)
        if result == "test message":
            print("✅ 消息提取功能正常")
            return True
        else:
            print(f"❌ 消息提取结果错误: {result}")
            return False

    except Exception as e:
        print(f"❌ BaseAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thread_safe_singleton():
    """测试 3: 验证线程安全单例"""
    print("\n" + "="*60)
    print("测试 3: 验证线程安全单例")
    print("="*60)

    try:
        from youyou.core.database import get_database, _db_lock

        # 验证锁存在
        if _db_lock is None:
            print("❌ 缺少 _db_lock")
            return False

        print("✅ _db_lock 存在")

        # 多线程并发测试
        instances = []

        def get_db_instance():
            db = get_database()
            instances.append(id(db))
            return db

        print("测试多线程并发获取数据库实例...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_db_instance) for _ in range(20)]
            for future in as_completed(futures):
                future.result()

        # 验证所有实例ID相同
        unique_ids = set(instances)
        if len(unique_ids) == 1:
            print(f"✅ 20个并发请求获得同一个实例 (ID: {list(unique_ids)[0]})")
            return True
        else:
            print(f"❌ 获得了 {len(unique_ids)} 个不同的实例: {unique_ids}")
            return False

    except Exception as e:
        print(f"❌ 线程安全测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_confusion_fix():
    """测试 4: 验证记忆混淆修复"""
    print("\n" + "="*60)
    print("测试 4: 验证记忆混淆 Bug 修复")
    print("="*60)

    try:
        from youyou.core.database import get_database
        from youyou.config import config

        db = get_database()

        # 测试场景: 记录两个不相关的物品
        print("\n场景 1: 记录两个不相关的物品")

        # 记录物品1
        result1 = db.remember_item("梳妆台", "卧室", config.USER_ID)
        print(f"记录物品1: {result1}")

        # 记录物品2
        result2 = db.remember_item("电视遥控器", "客厅", config.USER_ID)
        print(f"记录物品2: {result2}")

        # 查询不存在的物品 "时光机"
        print("\n查询不存在的物品 '时光机'...")
        result = db.query_item("时光机", config.USER_ID)
        print(f"查询结果: {result}")

        # 验证结果
        if result.get("status") == "not_found":
            print("✅ 正确返回 not_found (未混淆)")
            return True
        elif result.get("status") == "success":
            item_name = result.get("item", "")
            print(f"❌ 错误返回了物品: {item_name} (发生混淆)")
            return False
        else:
            print(f"❌ 未知状态: {result.get('status')}")
            return False

    except Exception as e:
        print(f"❌ 记忆混淆测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print(" "*20 + "修复效果测试")
    print("="*70)

    results = {}

    # 运行所有测试
    results['目录结构简化'] = test_import_structure()
    results['消息提取逻辑'] = test_base_agent_method()
    results['线程安全单例'] = test_thread_safe_singleton()
    results['记忆混淆修复'] = test_memory_confusion_fix()

    # 汇总结果
    print("\n" + "="*70)
    print(" "*25 + "测试汇总")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} : {status}")

    print("="*70)

    # 计算通过率
    passed_count = sum(1 for passed in results.values() if passed)
    total_count = len(results)
    pass_rate = (passed_count / total_count) * 100

    print(f"\n通过率: {passed_count}/{total_count} ({pass_rate:.1f}%)")

    if passed_count == total_count:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
