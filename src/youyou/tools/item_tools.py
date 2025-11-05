"""物品管理工具函数"""
from typing import Dict, Any
from datetime import datetime
from youyou.core.memory import memory_manager


def remember_item_location(item: str, location: str) -> Dict[str, Any]:
    """记录物品位置"""
    try:
        print(f"[物品工具] 记录物品位置: {item} -> {location}")
        content = f"{item}在{location}"
        metadata = {
            "type": "item_location",
            "item": item,
            "location": location,
            "timestamp": datetime.now().isoformat()
        }

        result = memory_manager.add(content=content, metadata=metadata)
        print(f"[物品工具] 记忆系统返回: {result}")

        if result.get("status") == "success":
            print(f"[物品工具] ✓ 成功记录物品位置")
            return {
                "status": "success",
                "message": f"已记住: {item}在{location}",
                "item": item,
                "location": location
            }
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


def query_item_location(item: str) -> Dict[str, Any]:
    """查询物品位置"""
    try:
        print(f"\n[物品工具] 🔍 查询物品位置: {item}")
        query = f"{item}在哪里"
        print(f"[物品工具] 搜索查询: {query}")
        results = memory_manager.search(query=query, limit=1)
        print(f"[物品工具] 搜索结果数量: {len(results) if results else 0}")
        if results:
            print(f"[物品工具] 搜索结果详情: {results}")

        if results and len(results) > 0:
            memory = results[0]

            if "metadata" in memory and "location" in memory["metadata"]:
                location = memory["metadata"]["location"]
                timestamp = memory["metadata"].get("timestamp", "")

                return {
                    "status": "success",
                    "item": item,
                    "location": location,
                    "timestamp": timestamp,
                    "message": f"{item}在{location}"
                }
            else:
                content = memory.get("memory", memory.get("content", ""))
                return {"status": "success", "item": item, "message": content}
        else:
            return {
                "status": "not_found",
                "item": item,
                "message": f"没有找到关于{item}的位置记录"
            }

    except Exception as e:
        return {"status": "error", "message": f"查询失败: {str(e)}"}


def list_all_items() -> Dict[str, Any]:
    """列出所有已记录的物品"""
    try:
        all_memories = memory_manager.get_all()
        items = []

        for memory in all_memories:
            if "metadata" in memory and memory["metadata"].get("type") == "item_location":
                item_name = memory["metadata"].get("item")
                location = memory["metadata"].get("location")
                timestamp = memory["metadata"].get("timestamp", "")

                if item_name and location:
                    items.append({
                        "item": item_name,
                        "location": location,
                        "timestamp": timestamp
                    })

        if items:
            return {
                "status": "success",
                "count": len(items),
                "items": items,
                "message": f"共找到 {len(items)} 个物品记录"
            }
        else:
            return {
                "status": "success",
                "count": 0,
                "items": [],
                "message": "还没有任何物品记录"
            }

    except Exception as e:
        return {"status": "error", "message": f"列出物品失败: {str(e)}"}


def update_item_location(item: str, new_location: str) -> Dict[str, Any]:
    """更新物品位置"""
    return remember_item_location(item, new_location)
