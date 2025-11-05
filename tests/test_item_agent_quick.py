"""ItemAgent 快速测试 - 核心场景"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"


def send(msg: str):
    """发送消息"""
    try:
        r = requests.post(f"{BASE_URL}/chat/message", json={"message": msg}, timeout=30)
        return r.json().get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


print("\n" + "="*80)
print("ItemAgent 快速测试")
print("="*80)

time.sleep(2)

# 测试1: 基础记录和查询
print("\n【测试1】基础记录和查询")
print("-"*80)
r1 = send("护照在卧室保险柜")
print(f"记录: {r1[:50]}...")
time.sleep(1)

r2 = send("护照在哪？")
print(f"查询: {r2}")
test1 = "保险柜" in r2 or "卧室" in r2
print(f"结果: {'✅ 通过' if test1 else '❌ 失败'}")

# 测试2: 区分相似物品
print("\n【测试2】区分相似物品")
print("-"*80)
send("家门钥匙在玄关")
time.sleep(1)
send("车钥匙在茶几")
time.sleep(1)

r3 = send("家门钥匙在哪？")
print(f"家门钥匙: {r3}")
test2a = "玄关" in r3

time.sleep(1)
r4 = send("车钥匙在哪？")
print(f"车钥匙: {r4}")
test2b = "茶几" in r4

print(f"结果: {'✅ 通过' if (test2a and test2b) else '❌ 失败'}")

# 测试3: 位置更新
print("\n【测试3】位置更新")
print("-"*80)
send("雨伞在门口")
time.sleep(1)
send("雨伞现在在阳台")
time.sleep(1)

r5 = send("雨伞在哪？")
print(f"更新后: {r5}")
test3 = "阳台" in r5
print(f"结果: {'✅ 通过' if test3 else '❌ 失败'}")

# 测试4: 未找到
print("\n【测试4】查询不存在的物品")
print("-"*80)
r6 = send("时光机在哪？")
print(f"查询: {r6}")
test4 = "没有" in r6 or "找不到" in r6 or "未记录" in r6
print(f"结果: {'✅ 通过' if test4 else '❌ 失败'}")

# 测试5: 多样化查询
print("\n【测试5】多样化查询方式")
print("-"*80)
send("笔记本电脑在书桌")
time.sleep(1)

queries = [
    "笔记本电脑在哪？",
    "电脑在哪？",
    "笔记本在哪儿？",
]

success = 0
for q in queries:
    r = send(q)
    if "书桌" in r:
        success += 1
        print(f"  ✅ '{q}' → {r[:30]}...")
    else:
        print(f"  ❌ '{q}' → {r[:30]}...")
    time.sleep(1)

test5 = success >= 2
print(f"结果: {success}/3 成功, {'✅ 通过' if test5 else '❌ 失败'}")

# 测试6: 列出所有物品
print("\n【测试6】列出所有物品")
print("-"*80)
send("手表在梳妆台")
time.sleep(1)
send("钱包在包里")
time.sleep(1)

r7 = send("我记录了哪些物品？")
print(f"列表: {r7[:100]}...")

# 检查是否包含至少几个物品
items_found = sum(1 for item in ["手表", "钱包", "护照", "钥匙", "雨伞"] if item in r7)
test6 = items_found >= 3
print(f"找到 {items_found} 个物品")
print(f"结果: {'✅ 通过' if test6 else '❌ 失败'}")

# 测试7: 复杂位置
print("\n【测试7】复杂位置描述")
print("-"*80)
send("身份证在卧室衣柜右侧第二个抽屉")
time.sleep(1)

r8 = send("身份证在哪？")
print(f"查询: {r8}")
test7 = "衣柜" in r8 or "抽屉" in r8
print(f"结果: {'✅ 通过' if test7 else '❌ 失败'}")

# 总结
print("\n" + "="*80)
print("📊 测试总结")
print("="*80)

results = [test1, test2a and test2b, test3, test4, test5, test6, test7]
passed = sum(results)
total = len(results)

print(f"通过: {passed}/{total}")
print(f"通过率: {passed/total*100:.1f}%")

print("\n详细:")
tests = [
    ("基础记录和查询", test1),
    ("区分相似物品", test2a and test2b),
    ("位置更新", test3),
    ("未找到物品", test4),
    ("多样化查询", test5),
    ("列出所有物品", test6),
    ("复杂位置", test7),
]

for i, (name, result) in enumerate(tests, 1):
    status = "✅" if result else "❌"
    print(f"{i}. {status} {name}")

print("\n" + "="*80)
if passed == total:
    print("🎉 所有测试通过！")
elif passed >= total * 0.7:
    print("👍 大部分测试通过！")
else:
    print("⚠️  需要改进。")
print("="*80)
