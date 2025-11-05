"""ItemAgent 专用工具"""
from langchain_core.tools import tool

from youyou.tools.item_tools import (
    remember_item_location as _remember_item_location,
    query_item_location as _query_item_location,
    list_all_items as _list_all_items,
)


@tool
def remember_item_location(item: str, location: str) -> str:
    """记录物品的位置信息

    Args:
        item: 物品名称
        location: 物品位置

    Returns:
        记录结果的消息
    """
    result = _remember_item_location(item, location)
    return result.get("message", "操作失败")


@tool
def query_item_location(item: str) -> str:
    """查询物品的位置

    Args:
        item: 要查询的物品名称

    Returns:
        物品位置信息
    """
    result = _query_item_location(item)
    return result.get("message", "查询失败")


@tool
def list_all_items() -> str:
    """列出所有已记录的物品及其位置

    Returns:
        所有物品的列表信息
    """
    result = _list_all_items()
    if result["status"] == "success" and result["count"] > 0:
        items = result["items"]
        items_text = "\n".join([f"- {item['item']}: {item['location']}" for item in items])
        return f"共有 {result['count']} 个物品:\n{items_text}"
    else:
        return result.get("message", "没有物品记录")
