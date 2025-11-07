"""统一日志配置模块

使用 loguru 提供强大、美观、易用的日志功能。

特性:
- 彩色控制台输出
- 自动日志轮转和压缩
- 异常追踪美化
- 支持不同日志级别
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "youyou.log",
    console_output: bool = True,
    file_output: bool = True,
    rotation: str = "10 MB",
    retention: str = "7 days",
    compression: str = "zip"
):
    """配置全局日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录
        log_file: 日志文件名
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        rotation: 日志轮转策略 (如: "10 MB", "00:00", "1 week")
        retention: 日志保留时间 (如: "7 days", "1 month")
        compression: 压缩格式 (如: "zip", "gz", "tar.gz")

    Returns:
        配置好的 logger 实例
    """
    # 移除默认 handler
    logger.remove()

    # 控制台输出格式（彩色）
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 文件输出格式（无颜色）
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # 添加控制台输出
    if console_output:
        logger.add(
            sys.stderr,
            level=log_level,
            format=console_format,
            colorize=True,
            backtrace=True,  # 显示异常的完整追踪
            diagnose=True,  # 显示变量值
        )

    # 添加文件输出
    if file_output:
        # 确保日志目录存在
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path / log_file,
            level=log_level,
            format=file_format,
            rotation=rotation,  # 自动轮转
            retention=retention,  # 保留时间
            compression=compression,  # 压缩旧日志
            backtrace=True,
            diagnose=True,
            enqueue=True,  # 异步写入，提高性能
        )

    return logger


def get_logger(name: str = None):
    """获取 logger 实例

    Args:
        name: logger 名称（通常是模块名）

    Returns:
        logger 实例

    Example:
        >>> from core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello")
    """
    if name:
        return logger.bind(name=name)
    return logger


# 配置拦截器，捕获标准 logging 模块的日志
class InterceptHandler:
    """拦截标准 logging 模块的日志，转发到 loguru"""

    def __init__(self, level=0):
        self._level = level

    def write(self, message):
        """拦截 print() 和 sys.stderr.write()"""
        # 过滤空消息和换行符
        message = message.strip()
        if message:
            logger.opt(depth=1).info(message)

    def flush(self):
        """兼容文件接口"""
        pass


def intercept_standard_logging():
    """拦截标准 logging 模块的日志

    这样其他使用标准 logging 的库（如 Flask、requests）
    的日志也会被 loguru 捕获和格式化。
    """
    import logging

    class LoguruInterceptHandler(logging.Handler):
        def emit(self, record):
            # 获取对应的 loguru level
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # 查找调用者
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # 移除所有现有的 handler
    logging.root.handlers = []

    # 添加拦截 handler
    logging.root.addHandler(LoguruInterceptHandler())

    # 设置级别
    logging.root.setLevel(logging.INFO)


# 默认初始化（可以在 main 函数中重新配置）
_default_logger = setup_logger()


__all__ = [
    "logger",
    "setup_logger",
    "get_logger",
    "intercept_standard_logging",
    "InterceptHandler"
]
