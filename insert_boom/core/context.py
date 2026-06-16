"""
运行时上下文 — 全流程共享的"记事本"

为什么需要它？
    14 个步骤之间要传递信息，比如:
    - Step2 放完炸药 → Step3 才能缩电缸
    - Step1 确认绕线器在初始位 → Step10 才能缠膜
    用 WorkflowContext 集中存放这些状态，避免全局变量混乱。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional

from insert_boom.core.events import WorkflowEvent, WorkflowState
from insert_boom.log_helper import get_logger

if TYPE_CHECKING:
    from insert_boom.hardware.hardware_manager import HardwareManager
    from insert_boom.robot.arm_left import LeftArm
    from insert_boom.robot.arm_right import RightArm

logger = get_logger("context")


@dataclass
class WorkflowContext:
    """流程运行时上下文 — 贯穿始终的共享数据"""

    # ---- 设备句柄（main.py 启动时注入）----
    hw: Optional["HardwareManager"] = None       # 步进电机、电缸、传感器
    left_arm: Optional["LeftArm"] = None         # 左臂 172.16.0.89
    right_arm: Optional["RightArm"] = None         # 右臂 172.16.0.88

    # ---- 流程运行状态 ----
    state: WorkflowState = WorkflowState.IDLE
    current_step: int = 0
    abort_requested: bool = False                  # True = 用户按了急停/中断

    # ---- 步骤间传递的"完成标志" ----
    # 前一步做完 → 置 True → 后一步 pre_check 才放行
    winder_at_home: bool = False       # Step1: 绕线器在初始位
    explosive_in_slot: bool = False    # Step2: 炸药已放入槽
    detonator_in_slot: bool = False    # Step4: 雷管已放入槽
    detonator_clamped: bool = False    # Step5: 电缸1已夹住雷管
    product_picked: bool = False       # Step13: 成品已取走

    # ---- 配置文件内容（从 YAML 加载）----
    system_config: dict = field(default_factory=dict)
    workflow_config: dict = field(default_factory=dict)

    # ---- 事件监听（控制台打印、未来可接 UI）----
    event_listeners: List[Callable[[WorkflowEvent], None]] = field(default_factory=list)

    def emit(self, event: WorkflowEvent) -> None:
        """广播事件 — 让控制台/UI 知道发生了什么"""
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as exc:
                logger.warning("事件监听异常: %s", exc)

    def request_abort(self) -> None:
        """急停 — 停止流程并让所有电机/电缸立刻停"""
        logger.warning("!!! 流程中止请求 !!!")
        self.abort_requested = True
        if self.hw is not None:
            self.hw.emergency_stop()

    def check_abort(self) -> bool:
        return self.abort_requested

    def get_step_config(self, step_key: str) -> dict:
        """读取 workflow.yaml 里某个步骤的参数（速度、超时等）"""
        return self.workflow_config.get("steps", {}).get(step_key, {})

    def log_flags(self) -> None:
        """调试用: 打印当前所有完成标志的状态"""
        logger.info(
            "状态标志: 绕线器=%s 炸药=%s 雷管=%s 夹持=%s 成品=%s",
            self.winder_at_home,
            self.explosive_in_slot,
            self.detonator_in_slot,
            self.detonator_clamped,
            self.product_picked,
        )
