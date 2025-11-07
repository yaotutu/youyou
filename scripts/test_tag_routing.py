"""测试标记路由功能"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.tag_parser import TagParser


def test_tag_parser():
    """测试 TagParser 的解析功能"""
    print("\n" + "=" * 60)
    print("测试 TagParser 解析功能")
    print("=" * 60)

    test_cases = [
        # 笔记标记
        "#note 记一下这个想法：Python 装饰器很强大",
        "#笔记 Rust 的所有权系统",
        "/note 保存这段代码",
        "/笔记 学习笔记",

        # GitHub 标记
        "#github https://github.com/langchain-ai/langchain",

        # 自动识别 GitHub URL
        "https://github.com/fastapi/fastapi",
        "看看这个项目：github.com/pytorch/pytorch 很不错",

        # 普通消息（无标记）
        "钥匙在哪里？",
        "记一下钥匙在桌上",  # 注意：这个应该被识别为物品记录，不是笔记
    ]

    for message in test_cases:
        print(f"\n输入: {message}")
        result = TagParser.parse(message)

        print(f"  has_tag: {result.has_tag}")
        if result.has_tag:
            print(f"  target_agent: {result.target_agent}")
            print(f"  tag_type: {result.tag_type}")
            print(f"  clean_message: {result.clean_message}")
        print("-" * 60)


def test_github_url_extraction():
    """测试 GitHub URL 提取功能"""
    print("\n" + "=" * 60)
    print("测试 GitHub URL 提取功能")
    print("=" * 60)

    test_cases = [
        "https://github.com/langchain-ai/langchain",
        "github.com/pytorch/pytorch",
        "fastapi/fastapi",  # owner/repo 格式
        "看看这个项目 https://github.com/rustlang/rust 很不错",
    ]

    for message in test_cases:
        print(f"\n输入: {message}")
        url = TagParser.extract_github_url(message)
        print(f"  提取的 URL: {url}")


def test_supported_tags():
    """测试获取支持的标记列表"""
    print("\n" + "=" * 60)
    print("支持的标记列表")
    print("=" * 60)

    tags = TagParser.get_supported_tags()
    for tag, description in tags.items():
        print(f"  {tag:20} - {description}")


def main():
    """运行所有测试"""
    print("🚀 开始测试标记路由功能...")

    try:
        test_tag_parser()
        test_github_url_extraction()
        test_supported_tags()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
