"""Agent 回退检测工具"""
import re
from dataclasses import dataclass


@dataclass
class RedirectResult:
    """回退检测结果"""
    is_redirect: bool
    reason: str = ""


def detect_redirect(response: str) -> RedirectResult:
    """检测 Agent 响应是否包含回退标记

    Args:
        response: Agent 的响应文本

    Returns:
        RedirectResult: 回退检测结果

    Example:
        >>> result = detect_redirect("[REDIRECT:这是饮食建议问题，与日历提醒无关]")
        >>> result.is_redirect
        True
        >>> result.reason
        '这是饮食建议问题，与日历提醒无关'
    """
    if not response:
        return RedirectResult(is_redirect=False)

    # 检查前100个字符（回退标记应该在开头）
    header = response[:100]

    # 匹配 [REDIRECT:原因] 格式
    match = re.search(r'\[REDIRECT:([^\]]+)\]', header)
    if match:
        return RedirectResult(
            is_redirect=True,
            reason=match.group(1).strip()
        )

    return RedirectResult(is_redirect=False)


__all__ = ['detect_redirect', 'RedirectResult']
