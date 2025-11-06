"""调试 Zep 搜索功能"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "youyou"))

from core.zep_memory import get_zep_memory

def main():
    zep = get_zep_memory()
    
    # 添加测试消息
    print("\n1. 添加测试消息...")
    zep.add_interaction(
        user_input="钥匙放在客厅桌上了",
        assistant_response="好的，我记住了：钥匙在客厅桌上"
    )
    
    # 获取所有消息并打印
    print("\n2. 获取所有最近消息...")
    messages = zep.get_recent_context(limit=50)
    print(f"\n总共 {len(messages)} 条消息:")
    for i, msg in enumerate(messages[-5:], 1):  # 只显示最后5条
        print(f"\n[{i}]")
        print(f"  角色: {msg['role']}")
        print(f"  内容: {msg['content']}")
        print(f"  元数据: {msg.get('metadata', {})}")
    
    # 测试搜索
    print("\n3. 测试搜索...")
    query = "钥匙"
    print(f"搜索关键词: {query}")
    
    # 手动检查匹配
    print("\n手动检查匹配:")
    for i, msg in enumerate(messages[-5:], 1):
        content = msg['content']
        matched = query in content
        print(f"[{i}] 内容: '{content[:50]}...' -> 匹配: {matched}")
    
    # 调用搜索方法
    results = zep.search_memory(query, limit=3)
    print(f"\n搜索结果: {len(results)} 条")
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['content'][:80]}...")

if __name__ == "__main__":
    main()
