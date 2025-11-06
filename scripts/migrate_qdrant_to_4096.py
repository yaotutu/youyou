"""迁移 Qdrant 从 1024 维到 4096 维

由于 Qwen3-Embedding-8B 实际生成 4096 维向量，需要重新创建集合
"""
import sys
sys.path.insert(0, '/Users/yaotutu/Desktop/code/youyou/src')

from pathlib import Path
from youyou.config import Config
from youyou.agents.note_agent.storage import NoteStorage
from youyou.agents.note_agent.utils import NoteUtils


def migrate():
    """执行迁移"""
    print("=" * 70)
    print("Qdrant 向量维度迁移工具")
    print("=" * 70)
    print()

    config = Config()

    # 检查数据目录
    qdrant_path = Path(config.DATA_DIR) / "notes" / "qdrant"
    if not qdrant_path.exists():
        print("✓ Qdrant 目录不存在，无需迁移")
        return

    print(f"📂 Qdrant 路径: {qdrant_path}")
    print()

    # 确认操作
    print("⚠️  警告: 此操作将:")
    print("  1. 删除现有的 Qdrant 向量数据")
    print("  2. 重新创建 4096 维的集合")
    print("  3. 为所有已保存的笔记重新生成向量")
    print()

    response = input("是否继续? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ 已取消迁移")
        return

    print()
    print("🚀 开始迁移...")
    print("-" * 70)

    # Step 1: 删除旧的 Qdrant 数据
    print("\n[1/4] 删除旧的 Qdrant 数据...")
    import shutil
    shutil.rmtree(qdrant_path)
    print("✓ 旧数据已删除")

    # Step 2: 初始化新的存储（会自动创建 4096 维集合）
    print("\n[2/4] 创建新的 4096 维集合...")
    storage = NoteStorage(config)
    storage._ensure_initialized()
    print("✓ 新集合已创建")

    # Step 3: 获取所有笔记
    print("\n[3/4] 读取所有笔记...")
    all_notes = storage.list_notes(limit=1000)  # 假设不超过 1000 条
    print(f"✓ 找到 {len(all_notes)} 条笔记")

    if len(all_notes) == 0:
        print("\n🎉 迁移完成（无笔记需要处理）")
        return

    # Step 4: 为每条笔记重新生成向量并保存
    print("\n[4/4] 重新生成向量...")
    utils = NoteUtils(config)

    success_count = 0
    failed_count = 0

    for i, note in enumerate(all_notes, 1):
        try:
            print(f"\n处理 [{i}/{len(all_notes)}]: {note.title[:50]}...")

            # 重新生成向量
            vector = utils.generate_embedding(note.content)

            # 保存到 Qdrant
            storage._qdrant_client.upsert(
                collection_name=storage.COLLECTION_NAME,
                points=[{
                    "id": note.id,
                    "vector": vector,
                    "payload": {
                        "type": note.type.value,
                        "title": note.title,
                        "tags": note.tags
                    }
                }]
            )

            success_count += 1
            print(f"  ✓ 向量已保存 (维度: {len(vector)})")

        except Exception as e:
            failed_count += 1
            print(f"  ❌ 失败: {e}")

    # 总结
    print()
    print("=" * 70)
    print("迁移完成")
    print("=" * 70)
    print(f"✓ 成功: {success_count} 条")
    if failed_count > 0:
        print(f"❌ 失败: {failed_count} 条")
    print()
    print("💡 提示: 现在可以重启 youyou-server，向量搜索功能将正常工作")


if __name__ == "__main__":
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
