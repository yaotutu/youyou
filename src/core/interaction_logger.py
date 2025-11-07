"""交互日志记录模块

记录完整的用户交互流程，用于后期分析和路由校准。
"""

import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from config import config
from core.logger import logger


@dataclass
class InteractionLog:
    """交互日志数据结构"""
    # 基本信息
    user_id: str
    timestamp: str
    user_input: str
    input_length: int

    # 路由信息
    routing_stage: str  # 'tag', 'keyword', 'supervisor'
    routing_matched: bool
    routing_keywords: Optional[str] = None  # JSON 字符串
    target_agent: Optional[str] = None

    # 回退信息
    redirect_occurred: bool = False
    redirect_reason: Optional[str] = None
    final_agent: Optional[str] = None

    # 响应信息
    response_text: Optional[str] = None
    response_length: Optional[int] = None
    response_time_ms: Optional[int] = None

    # 状态
    status: str = 'success'  # 'success', 'error', 'redirect'
    error_message: Optional[str] = None

    # 辅助字段
    created_date: Optional[str] = None  # YYYY-MM-DD

    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.fromisoformat(self.timestamp).strftime('%Y-%m-%d')


class InteractionLogger:
    """交互日志记录器"""

    DB_FILE = "interaction_logs.db"

    def __init__(self, data_dir: Path = None):
        """初始化日志记录器

        Args:
            data_dir: 数据目录，默认使用 config.DATA_DIR
        """
        self.data_dir = data_dir or config.DATA_DIR
        self.db_path = self.data_dir / self.DB_FILE
        self._initialized = False

    def _ensure_initialized(self):
        """确保数据库已初始化"""
        if self._initialized:
            return

        self.data_dir.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- 基本信息
                    user_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

                    -- 用户输入
                    user_input TEXT NOT NULL,
                    input_length INTEGER,

                    -- 路由信息
                    routing_stage TEXT,
                    routing_matched BOOLEAN,
                    routing_keywords TEXT,
                    target_agent TEXT,

                    -- 回退信息
                    redirect_occurred BOOLEAN DEFAULT 0,
                    redirect_reason TEXT,
                    final_agent TEXT,

                    -- 响应信息
                    response_text TEXT,
                    response_length INTEGER,
                    response_time_ms INTEGER,

                    -- 状态
                    status TEXT,
                    error_message TEXT,

                    -- 索引字段
                    created_date TEXT
                )
            """)

            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON interaction_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_user_id ON interaction_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_created_date ON interaction_logs(created_date)",
                "CREATE INDEX IF NOT EXISTS idx_routing_stage ON interaction_logs(routing_stage)",
                "CREATE INDEX IF NOT EXISTS idx_target_agent ON interaction_logs(target_agent)",
                "CREATE INDEX IF NOT EXISTS idx_redirect_occurred ON interaction_logs(redirect_occurred)",
            ]

            for idx_sql in indexes:
                cursor.execute(idx_sql)

            conn.commit()

        self._initialized = True
        logger.debug(f"[交互日志] 数据库已初始化: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def log(self, interaction: InteractionLog):
        """记录交互日志

        Args:
            interaction: 交互日志对象
        """
        try:
            self._ensure_initialized()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                data = asdict(interaction)

                cursor.execute("""
                    INSERT INTO interaction_logs (
                        user_id, timestamp, user_input, input_length,
                        routing_stage, routing_matched, routing_keywords, target_agent,
                        redirect_occurred, redirect_reason, final_agent,
                        response_text, response_length, response_time_ms,
                        status, error_message, created_date
                    ) VALUES (
                        :user_id, :timestamp, :user_input, :input_length,
                        :routing_stage, :routing_matched, :routing_keywords, :target_agent,
                        :redirect_occurred, :redirect_reason, :final_agent,
                        :response_text, :response_length, :response_time_ms,
                        :status, :error_message, :created_date
                    )
                """, data)

                conn.commit()
                log_id = cursor.lastrowid

            logger.debug(f"[交互日志] 已记录交互 #{log_id}")
            return log_id
        except Exception as e:
            logger.error(f"[交互日志] 记录失败: {e}")
            return None

    def query(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        routing_stage: Optional[str] = None,
        target_agent: Optional[str] = None,
        redirect_occurred: Optional[bool] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询交互日志

        Args:
            user_id: 用户ID
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            routing_stage: 路由阶段
            target_agent: 目标Agent
            redirect_occurred: 是否发生回退
            status: 状态
            limit: 最大返回数量

        Returns:
            日志列表
        """
        self._ensure_initialized()

        conditions = []
        params = {}

        if user_id:
            conditions.append("user_id = :user_id")
            params['user_id'] = user_id

        if start_date:
            conditions.append("created_date >= :start_date")
            params['start_date'] = start_date

        if end_date:
            conditions.append("created_date <= :end_date")
            params['end_date'] = end_date

        if routing_stage:
            conditions.append("routing_stage = :routing_stage")
            params['routing_stage'] = routing_stage

        if target_agent:
            conditions.append("target_agent = :target_agent")
            params['target_agent'] = target_agent

        if redirect_occurred is not None:
            conditions.append("redirect_occurred = :redirect_occurred")
            params['redirect_occurred'] = 1 if redirect_occurred else 0

        if status:
            conditions.append("status = :status")
            params['status'] = status

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM interaction_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """, {**params, 'limit': limit})

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息

        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            统计数据字典
        """
        self._ensure_initialized()

        conditions = []
        params = {}

        if start_date:
            conditions.append("created_date >= :start_date")
            params['start_date'] = start_date

        if end_date:
            conditions.append("created_date <= :end_date")
            params['end_date'] = end_date

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 总体统计
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_interactions,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(CASE WHEN redirect_occurred = 1 THEN 1 ELSE 0 END) as redirect_count,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
                FROM interaction_logs
                WHERE {where_clause}
            """, params)

            overall = dict(cursor.fetchone())

            # 路由阶段统计
            cursor.execute(f"""
                SELECT routing_stage, COUNT(*) as count
                FROM interaction_logs
                WHERE {where_clause}
                GROUP BY routing_stage
            """, params)

            routing_stats = {row['routing_stage']: row['count'] for row in cursor.fetchall()}

            # Agent 统计
            cursor.execute(f"""
                SELECT target_agent, COUNT(*) as count
                FROM interaction_logs
                WHERE {where_clause} AND target_agent IS NOT NULL
                GROUP BY target_agent
            """, params)

            agent_stats = {row['target_agent']: row['count'] for row in cursor.fetchall()}

            # 回退统计（按 Agent 分组）
            cursor.execute(f"""
                SELECT target_agent, COUNT(*) as redirect_count
                FROM interaction_logs
                WHERE {where_clause} AND redirect_occurred = 1
                GROUP BY target_agent
            """, params)

            redirect_by_agent = {row['target_agent']: row['redirect_count'] for row in cursor.fetchall()}

            # 计算误匹配率
            mismatch_rate = {}
            for agent, total in agent_stats.items():
                redirects = redirect_by_agent.get(agent, 0)
                mismatch_rate[agent] = round(redirects / total * 100, 2) if total > 0 else 0

            return {
                'overall': overall,
                'routing_stats': routing_stats,
                'agent_stats': agent_stats,
                'redirect_by_agent': redirect_by_agent,
                'mismatch_rate': mismatch_rate
            }

    def export_to_json(
        self,
        output_path: str,
        **query_kwargs
    ) -> int:
        """导出日志为 JSON

        Args:
            output_path: 输出文件路径
            **query_kwargs: 查询参数（传递给 query 方法）

        Returns:
            导出的记录数
        """
        logs = self.query(**query_kwargs)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        logger.info(f"[交互日志] 已导出 {len(logs)} 条记录到 {output_path}")
        return len(logs)

    def export_to_csv(
        self,
        output_path: str,
        **query_kwargs
    ) -> int:
        """导出日志为 CSV

        Args:
            output_path: 输出文件路径
            **query_kwargs: 查询参数（传递给 query 方法）

        Returns:
            导出的记录数
        """
        import csv

        logs = self.query(**query_kwargs)

        if not logs:
            logger.warning("[交互日志] 没有数据可导出")
            return 0

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)

        logger.info(f"[交互日志] 已导出 {len(logs)} 条记录到 {output_path}")
        return len(logs)


# 全局实例
_interaction_logger = None


def get_interaction_logger() -> InteractionLogger:
    """获取全局交互日志记录器实例"""
    global _interaction_logger
    if _interaction_logger is None:
        _interaction_logger = InteractionLogger()
    return _interaction_logger


__all__ = ['InteractionLogger', 'InteractionLog', 'get_interaction_logger']
