"""ItemAgent 专用工具

直接调用数据库层进行物品管理,无需中间封装层。
"""
from typing import Dict, Any
from langchain_core.tools import tool

from core.database import get_database
from core.zep_memory import get_zep_memory
from core.logger import logger
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
        logger.info(f"[物品工具] 记录物品位置: {item} -> {location}")

        # 使用数据库存储
        db = get_database()
        result = db.remember_item(
            item=item,
            location=location,
            user_id=config.USER_ID
        )

        logger.debug(f"[物品工具] 数据库返回: {result}")

        if result.get("status") == "success":
            action = result.get("action", "unknown")
            logger.success(f"[物品工具] ✓ 成功记录物品位置 (action: {action})")
            return result
        else:
            error_msg = result.get('message', '未知错误')
            logger.error(f"[物品工具] ✗ 记录失败: {error_msg}")
            return {
                "status": "error",
                "message": f"记录失败: {error_msg}"
            }

    except Exception as e:
        logger.exception(f"[物品工具] ✗ 异常: {e}")
        return {"status": "error", "message": f"记录失败: {str(e)}"}


def _query_item_location_impl(item: str) -> Dict[str, Any]:
    """
    查询物品位置的实现逻辑

    使用五级查询策略:
    1. 精确匹配 (normalized_name)
    2. 别名匹配 (item_aliases)
    3. FTS5 全文搜索
    4. LIKE 关键词模糊匹配
    5. Zep 语义搜索历史对话 (兜底)

    Args:
        item: 物品名称

    Returns:
        包含查询结果的字典
    """
    try:
        logger.info(f"[物品工具] 🔍 查询物品位置: {item}")

        # 级别 1-4: 使用数据库查询 (四级策略)
        db = get_database()
        result = db.query_item(
            item=item,
            user_id=config.USER_ID
        )

        logger.debug(f"[物品工具] 数据库返回: {result}")

        if result.get("status") == "success":
            match_type = result.get("match_type", "unknown")
            logger.success(f"[物品工具] ✓ 查询成功 (match_type: {match_type})")
            return result
        elif result.get("status") == "not_found":
            logger.info(f"[物品工具] ℹ SQLite 未找到物品，尝试 Zep 兜底查询...")

            # 级别 5: Zep 语义搜索兜底
            try:
                zep = get_zep_memory()
                memories = zep.search_memory(
                    query=f"用户提到 {item} 的位置、存放位置、放在哪里",
                    limit=3
                )

                if memories:
                    logger.success(f"[物品工具] ✓ Zep 找到 {len(memories)} 条相关记忆")

                    # 提取最相关的记忆
                    best_memory = memories[0]
                    context = best_memory['content']

                    return {
                        "status": "success",
                        "match_type": "zep_semantic",
                        "item": item,
                        "message": f"在历史对话中找到相关信息：{context}",
                        "zep_context": context,
                        "confidence": "low"  # 标记为低置信度
                    }
                else:
                    logger.info(f"[物品工具] ℹ Zep 也未找到相关记忆")

            except Exception as zep_error:
                logger.warning(f"[物品工具] ⚠️  Zep 查询失败: {zep_error}")

            # 所有方法都失败
            return result
        else:
            return {
                "status": "error",
                "message": f"查询失败: {result.get('message', '未知错误')}"
            }

    except Exception as e:
        logger.exception(f"[物品工具] ✗ 异常: {e}")
        return {"status": "error", "message": f"查询失败: {str(e)}"}


def _list_all_items_impl() -> Dict[str, Any]:
    """
    列出所有已记录的物品

    Returns:
        包含物品列表的字典
    """
    try:
        logger.info("[物品工具] 列出所有物品")

        # 使用数据库查询
        db = get_database()
        result = db.list_all_items(user_id=config.USER_ID)

        logger.info(f"[物品工具] 数据库返回: 共 {result.get('count', 0)} 个物品")

        return result

    except Exception as e:
        logger.exception(f"[物品工具] ✗ 异常: {e}")
        return {"status": "error", "message": f"列出物品失败: {str(e)}"}


# ========== LangChain Tool 封装 ==========

@tool
def remember_item_location(item: str, location: str) -> dict:
    """记录物品的位置信息

    Args:
        item: 物品名称
        location: 物品位置

    Returns:
        包含 action_type 和 data 的字典
    """
    result = _remember_item_location_impl(item, location)

    if result.get("status") != "success":
        return {
            "action_type": "error",
            "data": {"error": result.get("message", "操作失败")},
            "message": result.get("message", "操作失败")
        }

    # 根据 action 类型返回不同的消息格式
    action = result.get("action", "unknown")
    item_name = result.get("item", item)
    location_name = result.get("location", location)

    if action == "created":
        message = f"✅ 新记录成功：{item_name} 已记录在 {location_name}"
    elif action == "confirmed":
        message = f"⚠️ 重复记录提醒：{item_name} 之前已经记录在 {location_name} 了，位置没有变化"
    elif action == "moved":
        old_location = result.get("old_location", "")
        new_location = result.get("new_location", location_name)
        message = f"🔄 位置已更新：{item_name} 从 [{old_location}] 移到了 [{new_location}]"
    else:
        message = result.get("message", "操作完成")

    return {
        "action_type": "item_remembered",
        "data": {
            "item": item_name,
            "location": location_name,
            "action": action
        },
        "message": message
    }


@tool
def query_item_location(item: str) -> dict:
    """查询物品的位置

    Args:
        item: 要查询的物品名称

    Returns:
        包含 action_type 和 data 的字典
    """
    result = _query_item_location_impl(item)

    if result.get("status") == "success":
        return {
            "action_type": "item_location",
            "data": {
                "item": result.get("item", item),
                "location": result.get("location", ""),
                "match_type": result.get("match_type", "unknown")
            },
            "message": result.get("message", "查询成功")
        }
    else:
        return {
            "action_type": "error",
            "data": {"error": result.get("message", "查询失败")},
            "message": result.get("message", "查询失败")
        }


@tool
def list_all_items() -> dict:
    """列出所有已记录的物品及其位置

    Returns:
        包含 action_type 和 data 的字典
    """
    result = _list_all_items_impl()

    if result.get("status") == "success":
        count = result.get("count", 0)
        items = result.get("items", [])

        if count > 0:
            message = f"共有 {count} 个物品"
        else:
            message = "没有物品记录"

        return {
            "action_type": "item_list",
            "data": {
                "items": items,
                "count": count
            },
            "message": message
        }
    else:
        return {
            "action_type": "error",
            "data": {"error": result.get("message", "列出物品失败")},
            "message": result.get("message", "列出物品失败")
        }
