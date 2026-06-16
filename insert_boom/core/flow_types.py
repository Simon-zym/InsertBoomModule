"""
流程类型定义 — 供外部调用接口使用

同一时刻只能执行一种流程（由 FlowLock 保证）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FlowType(str, Enum):
    """可执行的流程类型"""

    # 完整装配流程 Step0~Step13（步进/电缸/双臂）
    ASSEMBLY = "assembly"

    # 左臂独立流程：取炸药 → 移至目标点（仅左臂，配置见 waypoints_left.yaml）
    LEFT_PICK_TRANSFER = "left_pick_transfer"


FLOW_DESCRIPTIONS = {
    FlowType.ASSEMBLY: "完整装配流程（14步，硬件+双臂）",
    FlowType.LEFT_PICK_TRANSFER: "左臂取炸药并移至目标点（仅左臂）",
}


def parse_flow_type(value: str) -> FlowType:
    """将字符串解析为 FlowType，支持枚举名或枚举值"""
    text = (value or "").strip().lower()
    for ft in FlowType:
        if text in (ft.value, ft.name.lower()):
            return ft
    valid = ", ".join(f.value for f in FlowType)
    raise ValueError(f"未知流程类型: '{value}'，可选: {valid}")


@dataclass
class RunResult:
    """流程执行结果 — 外部接口统一返回此结构"""

    success: bool
    flow_type: str
    message: str = ""
    failed_step: int = -1

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "flow_type": self.flow_type,
            "message": self.message,
            "failed_step": self.failed_step,
        }
