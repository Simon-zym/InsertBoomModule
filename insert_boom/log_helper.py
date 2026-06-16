"""
日志辅助 — 统一控制台与文件日志输出

用法:
    from insert_boom.log_helper import get_logger
    log = get_logger("robot")
    log.info("左臂已连接")
"""

from __future__ import annotations

import logging

# 项目统一日志名前缀，方便过滤: grep "insert_boom" log.txt
ROOT_LOGGER_NAME = "insert_boom"


def get_logger(module: str) -> logging.Logger:
    """
    获取子模块日志器

    module 示例: "main" / "engine" / "hardware" / "robot.left" / "step"
    """
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{module}")


def log_banner(logger: logging.Logger, title: str, lines: list[str]) -> None:
    """打印一段带分隔线的启动信息（关键配置一览）"""
    logger.info("=" * 50)
    logger.info(title)
    for line in lines:
        logger.info("  %s", line)
    logger.info("=" * 50)
