"""
配置加载工具 — 读取 config/ 目录下的 YAML 文件

所有配置文件都相对于项目根目录 InsertBoomModule/ 查找。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from insert_boom.log_helper import get_logger

logger = get_logger("config")


def get_project_root() -> Path:
    """返回项目根目录 InsertBoomModule/（与本文件所在 insert_boom/ 平级）"""
    return Path(__file__).resolve().parent.parent


def load_yaml(relative_path: str) -> Dict[str, Any]:
    """
    加载 YAML 配置文件

    Args:
        relative_path: 相对项目根的路径，如 "config/system.yaml"

    Returns:
        解析后的字典；空文件返回 {}
    """
    path = get_project_root() / relative_path
    if not path.exists():
        logger.error("配置文件不存在: %s", path)
        raise FileNotFoundError(f"配置文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    logger.info("已加载配置: %s", path)
    return data or {}
