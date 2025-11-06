"""测试 URL 解析"""
import re

def parse_github_url_old(url: str):
    """旧版本"""
    patterns = [
        r"github\.com/([^/]+)/([^/]+)",
        r"^([^/]+)/([^/]+)$"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            repo = repo.rstrip(".git")
            return owner, repo
    return None

def parse_github_url_new(url: str):
    """新版本（修复后）"""
    patterns = [
        r"github\.com/([^/]+)/([^/?#]+)",
        r"^([^/]+)/([^/?#]+)$"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo = match.groups()
            # 正确移除 .git 后缀
            if repo.endswith(".git"):
                repo = repo[:-4]
            repo = repo.split('#')[0].split('?')[0].strip()
            return owner, repo
    return None

# 测试用例
test_urls = [
    "https://github.com/fastapi/fastapi",
    "https://github.com/varun-raj/immich-power-tools",
    "github.com/langchain-ai/langchain",
    "fastapi/fastapi"
]

print("=" * 70)
print("URL 解析测试")
print("=" * 70)

for url in test_urls:
    print(f"\n测试: {url}")
    old_result = parse_github_url_old(url)
    new_result = parse_github_url_new(url)
    print(f"  旧版: {old_result}")
    print(f"  新版: {new_result}")
    if old_result != new_result:
        print("  ⚠️  结果不同！")
