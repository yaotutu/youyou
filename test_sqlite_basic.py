"""SQLite 基础功能测试"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def send(msg: str):
    """发送消息"""
    try:
        r = requests.post(f"{BASE_URL}/chat/message", json={"message": msg}, timeout=180)
        return r.json().get("response", "")
    except Exception as e:
        return f"ERROR: {e}"

print("\n" + "="*80)
print("SQLite 基础功能测试")
print("="*80)

# 测试1: 记录物品
print("\n【测试1】记录物品")
print("-"*80)
r1 = send("护照在卧室保险柜")
print(f"记录: {r1}")
time.sleep(2)

# 测试2: 查询物品
print("\n【测试2】查询物品")
print("-"*80)
r2 = send("护照在哪？")
print(f"查询: {r2}")
result1 = "保险柜" in r2 or "卧室" in r2
print(f"结果: {'✅ 通过' if result1 else '❌ 失败'}")
time.sleep(2)

# 测试3: 查询不存在的物品
print("\n【测试3】查询不存在的物品")
print("-"*80)
r3 = send("时光机在哪？")
print(f"查询: {r3}")
result2 = "没有" in r3 or "找不到" in r3 or "未" in r3
print(f"结果: {'✅ 通过' if result2 else '❌ 失败'}")
time.sleep(2)

# 测试4: 区分相似物品
print("\n【测试4】区分相似物品")
print("-"*80)
send("家门钥匙在玄关")
time.sleep(2)
send("车钥匙在茶几")
time.sleep(2)

r4a = send("家门钥匙在哪？")
print(f"家门钥匙: {r4a}")
result3a = "玄关" in r4a

r4b = send("车钥匙在哪？")
print(f"车钥匙: {r4b}")
result3b = "茶几" in r4b

print(f"结果: {'✅ 通过' if (result3a and result3b) else '❌ 失败'}")

# 总结
print("\n" + "="*80)
print("测试总结")
print("="*80)
results = [result1, result2, result3a and result3b]
passed = sum(results)
print(f"通过: {passed}/{len(results)}")
print(f"通过率: {passed/len(results)*100:.1f}%")
print("="*80)
