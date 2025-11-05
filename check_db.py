"""检查数据库内容"""
import sqlite3
from pathlib import Path

db_path = Path("data/items.db")

if not db_path.exists():
    print(f"数据库不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n" + "="*80)
print("数据库内容")
print("="*80)

cursor.execute("SELECT * FROM items WHERE is_deleted = 0 ORDER BY created_at DESC")
results = cursor.fetchall()

print(f"\n共有 {len(results)} 条记录:\n")

for row in results:
    row_dict = dict(row)
    print(f"ID: {row_dict['id']}")
    print(f"  物品名称: {row_dict['item_name']}")
    print(f"  规范化名: {row_dict['normalized_name']}")
    print(f"  位置: {row_dict['location']}")
    print(f"  创建时间: {row_dict['created_at']}")
    print(f"  更新时间: {row_dict['updated_at']}")
    print(f"  查询次数: {row_dict['query_count']}")
    print()

conn.close()
