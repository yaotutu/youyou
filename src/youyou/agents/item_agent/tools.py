"""ItemAgent 专用工具

直接调用数据库层进行物品管理,无需中间封装层。
"""
from typing import Dict, Any
from langchain_core.tools import tool

from core.database import get_database
from config import config


def _remember_item_location_impl(item: str, location: str) -> Dict[str, Any]:
    """
    记录物品位置的实现逻辑

    使用 SQLite 精确存储,自动处理重复物品:
    - 位置相同: 仅更新访问时间
    - 位置不同: 更新位置并记录历史

    Args:
        item: 物品名称
        location: 位置

    Returns:
        包含操作结果的字典
    """
    try:
        print(f"[物品工具] 记录物品位置: {item} -> {location}")

        # 使用数据库存储
        db = get_database()
        result = db.remember_item(
            item=item,
            location=location,
            user_id=config.USER_ID
        )

        print(f"[物品工具] 数据库返回: {result}")

        if result.get("status") == "success":
            action = result.get("action", "unknown")
            print(f"[物品工具] ✓ 成功记录物品位置 (action: {action})")
            return result
        else:
            error_msg = result.get('message', '未知错误')
            print(f"[物品工具] ✗ 记录失败: {error_msg}")
            return {
                "status": "error",
                "message": f"记录失败: {error_msg}"
            }

    except Exception as e:
        print(f"[物品工具] ✗ 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"记录失败: {str(e)}"}


def _query_item_location_impl(item: str) -> Dict[str, Any]:
    """
    查询物品位置的实现逻辑

    使用三级查询策略:
    1. 精确匹配 (normalized_name)
    2. 别名匹配 (item_aliases)
    3. FTS5 全文搜索

    Args:
        item: 物品名称

    Returns:
        包含查询结果的字典
    """
    try:
        print(f"\n[物品工具] 🔍 查询物品位置: {item}")

        # 使用数据库查询
        db = get_database()
        result = db.query_item(
            item=item,
            user_id=config.USER_ID
        )

        print(f"[物品工具] 数据库返回: {result}")

        if result.get("status") == "success":
            match_type = result.get("match_type", "unknown")
            print(f"[物品工具] ✓ 查询成功 (match_type: {match_type})")
            return result
        elif result.get("status") == "not_found":
            print(f"[物品工具] ℹ 未找到物品")
            return result
        else:
            return {
                "status": "error",
                "message": f"查询失败: {result.get('message', '未知错误')}"
            }

    except Exception as e:
        print(f"[物品工具] ✗ 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"查询失败: {str(e)}"}


def _list_all_items_impl() -> Dict[str, Any]:
    """
    列出所有已记录的物品

    Returns:
        包含物品列表的字典
    """
    try:
        print(f"[物品工具] 列出所有物品")

        # 使用数据库查询
        db = get_database()
        result = db.list_all_items(user_id=config.USER_ID)

        print(f"[物品工具] 数据库返回: 共 {result.get('count', 0)} 个物品")

        return result

    except Exception as e:
        print(f"[物品工具] ✗ 异常: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"列出物品失败: {str(e)}"}


# ========== LangChain Tool 封装 ==========

@tool
def remember_item_location(item: str, location: str) -> str:
    """记录物品的位置信息

    Args:
        item: 物品名称
        location: 物品位置

    Returns:
        记录结果的消息
    """
    result = _remember_item_location_impl(item, location)
    return result.get("message", "操作失败")


@tool
def query_item_location(item: str) -> str:
    """查询物品的位置

    Args:
        item: 要查询的物品名称

    Returns:
        物品位置信息
    """
    result = _query_item_location_impl(item)
    return result.get("message", "查询失败")


@tool
def list_all_items() -> str:
    """列出所有已记录的物品及其位置

    Returns:
        所有物品的列表信息
    """
    result = _list_all_items_impl()
    if result["status"] == "success" and result["count"] > 0:
        items = result["items"]
        items_text = "\n".join([f"- {item['item']}: {item['location']}" for item in items])
        return f"共有 {result['count']} 个物品:\n{items_text}"
    else:
        return result.get("message", "没有物品记录")
