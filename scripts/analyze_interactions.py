#!/usr/bin/env python3
"""交互日志分析脚本

提供统计、导出、可视化等功能。
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.interaction_logger import get_interaction_logger
from core.logger import logger


def show_statistics(start_date=None, end_date=None):
    """显示统计信息"""
    interaction_logger = get_interaction_logger()
    stats = interaction_logger.get_statistics(start_date, end_date)

    print("=" * 60)
    print("交互日志统计")
    print("=" * 60)

    overall = stats['overall']
    print(f"\n📊 总体统计:")
    print(f"  总交互次数: {overall['total_interactions']}")
    if overall['avg_response_time']:
        print(f"  平均响应时间: {overall['avg_response_time']:.2f} ms")
    else:
        print(f"  平均响应时间: N/A")
    print(f"  回退次数: {overall['redirect_count']}")
    print(f"  错误次数: {overall['error_count']}")

    if stats['routing_stats']:
        print(f"\n🔀 路由阶段统计:")
        for stage, count in stats['routing_stats'].items():
            print(f"  {stage}: {count}")

    if stats['agent_stats']:
        print(f"\n🤖 Agent 调用统计:")
        for agent, count in stats['agent_stats'].items():
            print(f"  {agent}: {count}")

    if stats['mismatch_rate']:
        print(f"\n⚠️  误匹配率 (回退率):")
        for agent, rate in stats['mismatch_rate'].items():
            redirects = stats['redirect_by_agent'].get(agent, 0)
            total = stats['agent_stats'][agent]
            print(f"  {agent}: {rate}% ({redirects}/{total})")

    print("=" * 60)


def export_logs(format_type, output_path, **query_kwargs):
    """导出日志"""
    interaction_logger = get_interaction_logger()

    if format_type == 'json':
        count = interaction_logger.export_to_json(output_path, **query_kwargs)
    elif format_type == 'csv':
        count = interaction_logger.export_to_csv(output_path, **query_kwargs)
    else:
        logger.error(f"不支持的格式: {format_type}")
        return

    print(f"✅ 已导出 {count} 条记录到 {output_path}")


def show_recent_redirects(limit=10):
    """显示最近的回退记录"""
    interaction_logger = get_interaction_logger()
    redirects = interaction_logger.query(redirect_occurred=True, limit=limit)

    print("=" * 80)
    print(f"最近 {len(redirects)} 次回退记录")
    print("=" * 80)

    for i, log in enumerate(redirects, 1):
        print(f"\n#{i} [{log['timestamp']}]")
        print(f"  用户输入: {log['user_input']}")
        print(f"  初始路由: {log['routing_stage']} -> {log['target_agent']}")
        print(f"  回退原因: {log['redirect_reason']}")
        print(f"  最终处理: {log['final_agent']}")
        print(f"  匹配关键词: {log['routing_keywords']}")


def show_mismatches_by_keyword():
    """按关键词分析误匹配"""
    interaction_logger = get_interaction_logger()
    redirects = interaction_logger.query(redirect_occurred=True, limit=1000)

    # 统计关键词误匹配
    keyword_mismatches = {}

    for log in redirects:
        if log['routing_keywords']:
            import json
            try:
                keywords = json.loads(log['routing_keywords'])
                for kw in keywords:
                    keyword_mismatches[kw] = keyword_mismatches.get(kw, 0) + 1
            except json.JSONDecodeError:
                pass

    print("=" * 60)
    print("关键词误匹配统计 (需要校准的关键词)")
    print("=" * 60)

    sorted_keywords = sorted(keyword_mismatches.items(), key=lambda x: x[1], reverse=True)

    for keyword, count in sorted_keywords:
        print(f"  {keyword}: {count} 次误匹配")


def main():
    parser = argparse.ArgumentParser(description='交互日志分析工具')
    parser.add_argument('action', choices=['stats', 'export', 'redirects', 'keywords'],
                        help='操作类型')
    parser.add_argument('--start-date', help='起始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                        help='导出格式')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--limit', type=int, default=10, help='限制数量')

    args = parser.parse_args()

    if args.action == 'stats':
        show_statistics(args.start_date, args.end_date)

    elif args.action == 'export':
        if not args.output:
            print("❌ 请指定输出路径: --output <path>")
            return

        export_logs(
            args.format,
            args.output,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=10000
        )

    elif args.action == 'redirects':
        show_recent_redirects(args.limit)

    elif args.action == 'keywords':
        show_mismatches_by_keyword()


if __name__ == '__main__':
    main()
