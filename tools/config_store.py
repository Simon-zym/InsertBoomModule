"""配置文件读写 — InsertBoom 配置编辑器共用模块"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILES: dict[str, dict[str, str]] = {
    "system": {
        "path": "config/system.yaml",
        "title": "系统硬件",
        "description": "串口、步进电机、电缸、传感器、夹爪、机械臂",
    },
    "workflow": {
        "path": "config/workflow.yaml",
        "title": "装配流程",
        "description": "重试、超时及各步骤运行参数",
    },
    "waypoints_left": {
        "path": "config/waypoints_left.yaml",
        "title": "左臂途径点",
        "description": "左臂各流程途径点与命名位姿",
    },
    "waypoints_right": {
        "path": "config/waypoints_right.yaml",
        "title": "右臂途径点",
        "description": "右臂各流程途径点与命名位姿",
    },
}


def resolve_path(config_id: str) -> Path:
    if config_id not in CONFIG_FILES:
        raise KeyError(f"未知配置: {config_id}")
    return PROJECT_ROOT / CONFIG_FILES[config_id]["path"]


def load_config(config_id: str) -> dict[str, Any]:
    path = resolve_path(config_id)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config_id: str, data: dict[str, Any]) -> Path:
    path = resolve_path(config_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(f".yaml.bak.{stamp}")
        shutil.copy2(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 由配置编辑器保存于 {datetime.now().isoformat(timespec='seconds')}\n")
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )
    return path
