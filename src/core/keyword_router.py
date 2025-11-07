"""关键词路由器 - 基于关键词的快速 Agent 路由

在调用 Supervisor（LLM 路由）之前，通过关键词匹配快速路由到特定 Agent。
这样可以：
1. 提高路由准确率（避免 LLM 误判）
2. 加快响应速度（减少 LLM 调用）
3. 降低成本（减少 API 调用）

当前支持的路由：
- calendar_agent: 日历提醒相关
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingResult:
    """路由结果"""
    matched: bool  # 是否匹配到关键词
    target_agent: Optional[str]  # 目标 Agent 名称（如果匹配）
    original_message: str  # 原始消息（不修改）
    matched_keywords: list[str]  # 匹配到的关键词（用于调试）


class KeywordRouter:
    """关键词路由器"""

    # Calendar Agent 的关键词规则
    # 1. 显式标记（最高优先级）
    CALENDAR_TAGS = [
        r'^#提醒\s*',
        r'^#calendar\s*',
        r'^#日历\s*',
        r'^#日程\s*',
        r'^/remind\s*',
        r'^/提醒\s*',
    ]

    # 2. 动作关键词
    CALENDAR_ACTION_KEYWORDS = [
        '提醒',
        '记得',
        '别忘了',
        '别忘记',
        '不要忘',
        '打卡',
        '日历',
        '日程',
        '会议',
        '预约',
        '安排',
    ]

    # 3. 时间表达式
    CALENDAR_TIME_EXPRESSIONS = [
        # 相对日期
        '今天',
        '明天',
        '后天',
        '大后天',
        '昨天',
        '前天',
        # 相对时间
        '今早',
        '今晚',
        '明早',
        '明晚',
        # 周相关
        '本周',
        '下周',
        '下下周',
        '上周',
        '周一',
        '周二',
        '周三',
        '周四',
        '周五',
        '周六',
        '周日',
        '星期一',
        '星期二',
        '星期三',
        '星期四',
        '星期五',
        '星期六',
        '星期日',
        # 时段
        '上午',
        '下午',
        '中午',
        '晚上',
        '早上',
        '傍晚',
        '深夜',
        '凌晨',
    ]

    # 时间点表达式（正则）
    CALENDAR_TIME_PATTERNS = [
        r'\d+[点時时]',  # 8点、9點、10时
        r'\d+:\d+',  # 8:00、14:30
        r'\d+月\d+[日号號]',  # 12月25日、1月1号
    ]

    @classmethod
    def match(cls, message: str) -> RoutingResult:
        """匹配消息并返回路由结果

        Args:
            message: 用户输入的原始消息

        Returns:
            RoutingResult: 路由结果
        """
        matched_keywords = []

        # 1. 检查显式标记（最高优先级）
        for tag_pattern in cls.CALENDAR_TAGS:
            if re.search(tag_pattern, message):
                matched_keywords.append(f'标记:{tag_pattern}')
                return RoutingResult(
                    matched=True,
                    target_agent='calendar_agent',
                    original_message=message,
                    matched_keywords=matched_keywords
                )

        # 2. 检查动作关键词
        action_matched = False
        for keyword in cls.CALENDAR_ACTION_KEYWORDS:
            if keyword in message:
                matched_keywords.append(f'动作:{keyword}')
                action_matched = True

        # 3. 检查时间表达式
        time_matched = False
        for time_expr in cls.CALENDAR_TIME_EXPRESSIONS:
            if time_expr in message:
                matched_keywords.append(f'时间:{time_expr}')
                time_matched = True

        # 4. 检查时间点表达式（正则）
        for time_pattern in cls.CALENDAR_TIME_PATTERNS:
            if re.search(time_pattern, message):
                matched_keywords.append(f'时间点:{time_pattern}')
                time_matched = True

        # 5. 路由决策
        # 优先级：动作关键词 > 动作+时间组合 > 单独时间词（需谨慎）
        if action_matched:
            # 有动作关键词，直接路由
            return RoutingResult(
                matched=True,
                target_agent='calendar_agent',
                original_message=message,
                matched_keywords=matched_keywords
            )

        # 只有时间词，没有动作词 - 需要更谨慎
        # 排除一些明显不是日历的场景
        non_calendar_patterns = [
            '天气',
            '温度',
            '穿什么',
            '吃什么',
            '做什么',
            '怎么样',
            '如何',
        ]

        if time_matched:
            # 检查是否包含排除关键词
            has_non_calendar = any(pattern in message for pattern in non_calendar_patterns)
            if not has_non_calendar:
                # 纯时间表达，可能是日历相关
                return RoutingResult(
                    matched=True,
                    target_agent='calendar_agent',
                    original_message=message,
                    matched_keywords=matched_keywords
                )

        # 没有匹配
        return RoutingResult(
            matched=False,
            target_agent=None,
            original_message=message,
            matched_keywords=[]
        )

    @classmethod
    def test(cls, test_cases: list[tuple[str, bool, str]]) -> dict:
        """测试关键词路由器

        Args:
            test_cases: 测试用例列表 [(消息, 应该匹配, 期望的agent), ...]

        Returns:
            测试结果统计
        """
        results = {
            'total': len(test_cases),
            'passed': 0,
            'failed': 0,
            'details': []
        }

        for message, should_match, expected_agent in test_cases:
            result = cls.match(message)
            is_correct = (
                result.matched == should_match and
                (not should_match or result.target_agent == expected_agent)
            )

            if is_correct:
                results['passed'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'message': message,
                'expected': {'matched': should_match, 'agent': expected_agent},
                'actual': {'matched': result.matched, 'agent': result.target_agent},
                'keywords': result.matched_keywords,
                'passed': is_correct
            })

        return results


# 导出
__all__ = ['KeywordRouter', 'RoutingResult']
