"""测试数据库写入"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from youyou.core.database import get_database

print("测试数据库写入...")

db = get_database()

print("\n尝试记录物品...")
result = db.remember_item(
    item="测试物品",
    location="测试位置",
    user_id="default"
)

print(f"结果: {result}")

if result['status'] == 'success':
    print("\n✓ 写入成功!")

    # 尝试查询
    result2 = db.query_item(item="测试物品", user_id="default")
    print(f"查询结果: {result2}")
else:
    print(f"\n✗ 写入失败: {result.get('message')}")
