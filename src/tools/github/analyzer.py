"""GitHub 项目分析工具"""
import re
import requests
from typing import Dict, Optional, Any
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI

from config import Config
from core.logger import logger


class GitHubAnalyzer:
    """GitHub 项目分析器"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.AGENT_MODEL,
            base_url=config.OPENAI_API_BASE,
            api_key=config.OPENAI_API_KEY,
            temperature=0
        )

    def _extract_repo_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从任意 GitHub URL 中提取仓库信息

        支持的 URL 类型：
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/branch/path
        - https://github.com/owner/repo/blob/branch/file
        - https://github.com/owner/repo/issues/123
        - https://github.com/owner/repo/pull/456
        - owner/repo

        Args:
            url: GitHub URL（任意格式）

        Returns:
            {
                "owner": "fastapi",
                "repo": "fastapi",
                "resource_type": "repo|directory|file|issue|pr",
                "path": "/tree/main/docs" (可选),
                "original_url": "https://github.com/..."
            }
        """
        original_url = url

        # 模式：匹配 github.com/owner/repo 以及后续的路径
        # 支持：/tree/branch/path, /blob/branch/file, /issues/123, /pull/456
        pattern = r'github\.com/([^/]+)/([^/?#]+)(?:/([^/?#]+)(?:/([^/?#]+))?)?'

        match = re.search(pattern, url)
        if match:
            owner = match.group(1)
            repo = match.group(2)
            resource_part = match.group(3) if len(match.groups()) >= 3 else None

            # 移除 .git 后缀
            if repo.endswith(".git"):
                repo = repo[:-4]

            # 判断资源类型
            resource_type = "repo"  # 默认
            path = None

            if resource_part:
                if resource_part == "tree":
                    resource_type = "directory"
                    # 提取路径部分
                    tree_match = re.search(r'/tree/[^/]+/(.*)', url)
                    if tree_match:
                        path = f"/tree/{tree_match.group(1)}"
                elif resource_part == "blob":
                    resource_type = "file"
                    blob_match = re.search(r'/blob/[^/]+/(.*)', url)
                    if blob_match:
                        path = f"/blob/{blob_match.group(1)}"
                elif resource_part == "issues":
                    resource_type = "issue"
                    issue_match = re.search(r'/issues/(\d+)', url)
                    if issue_match:
                        path = f"/issues/{issue_match.group(1)}"
                elif resource_part == "pull":
                    resource_type = "pr"
                    pr_match = re.search(r'/pull/(\d+)', url)
                    if pr_match:
                        path = f"/pull/{pr_match.group(1)}"

            return {
                "owner": owner,
                "repo": repo,
                "resource_type": resource_type,
                "path": path,
                "original_url": original_url
            }

        # 简写格式：owner/repo
        simple_pattern = r'^([^/]+)/([^/?#]+)$'
        simple_match = re.search(simple_pattern, url)
        if simple_match:
            owner, repo = simple_match.groups()
            if repo.endswith(".git"):
                repo = repo[:-4]
            return {
                "owner": owner,
                "repo": repo,
                "resource_type": "repo",
                "path": None,
                "original_url": original_url
            }

        return None

    def analyze_repo(self, github_url: str) -> Optional[Dict[str, Any]]:
        """
        分析 GitHub 仓库

        Args:
            github_url: GitHub URL（支持任意格式，自动提取仓库信息）

        Returns:
            包含分析结果的字典，失败返回 None
        """
        # 使用新的 URL 提取逻辑
        repo_info = self._extract_repo_info(github_url)
        if not repo_info:
            logger.error(f"[GitHub 分析器] ❌ 无法解析 URL: {github_url}")
            return None

        owner = repo_info["owner"]
        repo = repo_info["repo"]
        resource_type = repo_info["resource_type"]
        path = repo_info.get("path")
        original_url = repo_info["original_url"]

        # 日志输出
        logger.info(f"[GitHub 分析器] 📥 原始 URL: {original_url}")
        logger.debug(f"[GitHub 分析器] 🔍 提取仓库: {owner}/{repo}")
        logger.info(f"[GitHub 分析器] 📋 资源类型: {resource_type}" + (f" (路径: {path})" if path else ""))

        # 获取仓库元数据
        metadata = self._fetch_repo_metadata(owner, repo)
        if not metadata:
            return None

        # 获取 README 内容
        readme_content = self._fetch_readme(owner, repo)

        # 使用 LLM 分析项目
        analysis = self._analyze_with_llm(
            repo_name=f"{owner}/{repo}",
            readme=readme_content,
            metadata=metadata
        )

        return {
            "url": github_url,
            "owner": owner,
            "repo": repo,
            "metadata": metadata,
            "readme": readme_content,
            "analysis": analysis,
            # 新增：资源信息
            "resource_info": {
                "type": resource_type,
                "path": path,
                "original_url": original_url
            }
        }

    def _parse_github_url(self, url: str) -> Optional[tuple]:
        """解析 GitHub URL，提取 owner 和 repo"""
        # 支持多种格式：
        # - https://github.com/owner/repo
        # - github.com/owner/repo
        # - owner/repo

        patterns = [
            r"github\.com/([^/]+)/([^/?#]+)",  # 匹配直到 /、? 或 # 为止
            r"^([^/]+)/([^/?#]+)$"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner, repo = match.groups()
                # 移除可能的 .git 后缀（使用 removesuffix 而不是 rstrip！）
                if repo.endswith(".git"):
                    repo = repo[:-4]  # 移除 ".git"
                # 移除可能的 URL fragment
                repo = repo.split('#')[0].split('?')[0].strip()
                return owner, repo

        return None

    def _fetch_repo_metadata(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """获取仓库元数据（通过 GitHub API）"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description", ""),
                "language": data.get("language", ""),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "topics": data.get("topics", []),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "license": data.get("license", {}).get("name", "") if data.get("license") else "",
                "homepage": data.get("homepage", "")
            }
        except Exception as e:
            logger.error(f"[GitHub 分析器] 获取元数据失败: {e}")
            return None

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """获取 README 内容"""
        # 尝试多个常见的 README 文件名
        readme_names = ["README.md", "readme.md", "README", "readme"]

        for readme_name in readme_names:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{readme_name}"

            try:
                response = requests.get(raw_url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception:
                pass

            # 尝试 master 分支
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{readme_name}"
            try:
                response = requests.get(raw_url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception:
                pass

        return ""

    def _analyze_with_llm(
        self,
        repo_name: str,
        readme: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用 LLM 分析项目"""
        # 截断过长的 README
        max_readme_length = 4000
        if len(readme) > max_readme_length:
            readme = readme[:max_readme_length] + "\n...(内容已截断)"

        prompt = f"""请分析这个 GitHub 项目，提取关键信息。

项目名称: {repo_name}
描述: {metadata.get('description', '无')}
主要语言: {metadata.get('language', '未知')}
Star 数: {metadata.get('stars', 0)}
主题标签: {', '.join(metadata.get('topics', []))}

README 内容:
{readme}

请提取以下信息（以 JSON 格式返回）：
1. tech_stack: 使用的技术栈（数组，例如 ["Python", "FastAPI", "PostgreSQL"]）
2. purpose: 项目用途（简短描述，1-2 句话）
3. key_features: 核心功能（数组，3-5 个要点）
4. use_cases: 适用场景（数组，2-3 个场景）
5. summary: 项目总结（50 字以内）

只返回 JSON，不要其他内容。
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # 移除可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            import json
            analysis = json.loads(content.strip())

            return analysis
        except Exception as e:
            logger.error(f"[GitHub 分析器] LLM 分析失败: {e}")
            # 返回默认结构
            return {
                "tech_stack": [metadata.get("language", "未知")] if metadata.get("language") else [],
                "purpose": metadata.get("description", "未提供描述"),
                "key_features": [],
                "use_cases": [],
                "summary": metadata.get("description", "未提供描述")[:50]
            }
