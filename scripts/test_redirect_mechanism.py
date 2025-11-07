"""测试 Agent 回退机制"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import requests
import json
import time


def test_redirect():
    """测试回退机制"""
    api_url = "http://localhost:8000/api/v1/chat/message"

    test_cases = [
        # 应该正常处理（不回退）
        ("晚上八点提醒我打卡", "✅ 应该正常处理", "calendar"),
        ("明天上午9点提醒我开会", "✅ 应该正常处理", "calendar"),
        ("我今天有什么提醒", "✅ 应该正常处理", "calendar"),

        # 应该回退到 Supervisor
        ("明天吃什么", "🔄 应该回退（饮食建议）", "redirect"),
        ("今天天气怎么样", "🔄 应该回退（天气查询）", "redirect"),
        ("你好", "🔄 应该回退（一般问候）", "redirect"),

        # 不触发关键词，直接走 Supervisor
        ("钥匙在哪里", "📍 直接走 Supervisor（物品查询）", "supervisor"),
    ]

    print("="*80)
    print("🧪 测试 Agent 回退机制")
    print("="*80)
    print("\n提示：请确保服务器正在运行 (uv run youyou-server)")
    print("="*80)

    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for message, expected, test_type in test_cases:
        print(f"\n{'='*80}")
        print(f"📝 测试消息: {message}")
        print(f"🎯 预期: {expected}")
        print(f"🔖 类型: {test_type}")
        print("-"*80)

        try:
            response = requests.post(
                api_url,
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "")
                print(f"✓ 响应成功")
                print(f"📤 回复 (前150字):\n{reply[:150]}...")

                # 检查是否包含回退标记（不应该返回给用户）
                if "[REDIRECT:" in reply:
                    print("❌ 错误：响应中包含回退标记（不应该返回给用户）")
                    results["failed"] += 1
                    results["details"].append({
                        "message": message,
                        "expected": expected,
                        "status": "failed",
                        "reason": "响应包含回退标记"
                    })
                else:
                    print("✅ 响应正常（无回退标记）")
                    results["passed"] += 1
                    results["details"].append({
                        "message": message,
                        "expected": expected,
                        "status": "passed",
                        "reply": reply[:100]
                    })
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                print(f"   {response.text}")
                results["failed"] += 1
                results["details"].append({
                    "message": message,
                    "expected": expected,
                    "status": "failed",
                    "reason": f"HTTP {response.status_code}"
                })

        except Exception as e:
            print(f"✗ 请求异常: {e}")
            results["failed"] += 1
            results["details"].append({
                "message": message,
                "expected": expected,
                "status": "failed",
                "reason": str(e)
            })

        # 短暂延迟，避免请求过快
        time.sleep(0.5)

    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    print(f"总计: {results['total']} 项")
    print(f"通过: {results['passed']} 项 ✅")
    print(f"失败: {results['failed']} 项 ❌")
    print(f"成功率: {results['passed']/results['total']*100:.1f}%")

    print("\n" + "-"*80)
    print("📝 详细结果:")
    for detail in results["details"]:
        status_icon = "✅" if detail["status"] == "passed" else "❌"
        print(f"\n{status_icon} {detail['message']}")
        print(f"   预期: {detail['expected']}")
        if detail["status"] == "failed":
            print(f"   原因: {detail.get('reason', 'Unknown')}")

    print("\n" + "="*80)
    print("🎉 测试完成")
    print("="*80)
    print("\n💡 提示：请查看服务器日志了解详细的路由过程:")
    print("   tail -f /tmp/youyou_server.log | grep -E '(回退|REDIRECT|CalendarAgent)'")


if __name__ == "__main__":
    try:
        # 先检查服务器是否运行
        print("⏳ 检查服务器状态...")
        response = requests.get("http://localhost:8000/api/v1/system/health", timeout=2)
        if response.status_code == 200:
            print("✅ 服务器正在运行\n")
            test_redirect()
        else:
            print("❌ 服务器响应异常")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("\n请先启动服务器:")
        print("  uv run youyou-server")
