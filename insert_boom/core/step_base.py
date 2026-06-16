"""
步骤基类 — 所有装配步骤的模板

每个步骤都按相同顺序执行，像流水线一样：
    1. pre_check  先检查条件（例如：上一步做完了吗？硬件连上了吗？）
    2. execute    真正干活（例如：让机械臂运动、让步进电机转动）
    3. post_check 再确认结果（例如：传感器显示到位了吗？）
    如果失败 → on_error 记录原因，必要时 rollback 回退
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from insert_boom.core.context import WorkflowContext
from insert_boom.core.events import EventType, WorkflowEvent
from insert_boom.log_helper import get_logger

_step_logger = get_logger("step")


@dataclass
class StepResult:
    """单步执行结果 — success=True 表示这一步通过了"""

    success: bool
    message: str = ""


class StepBase(ABC):
    """
    步骤基类，子类必须填写:
        step_index  : 步骤编号 0~13
        step_key    : 在 workflow.yaml 里对应的配置名
        description : 中文说明，会显示在日志里
    """

    step_index: int = -1
    step_key: str = ""
    description: str = ""

    def log(self, ctx: WorkflowContext, message: str) -> None:
        """
        记录步骤日志（同时写控制台 + Python 日志）

        格式: [Step02] 左臂开始取炸药...
        """
        full_msg = f"[Step{self.step_index:02d}] {message}"
        _step_logger.info(full_msg)
        ctx.emit(
            WorkflowEvent(
                event_type=EventType.LOG,
                message=full_msg,
                step_index=self.step_index,
                step_name=self.step_key,
            )
        )

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        """
        前置检查 — 执行前先确认环境安全、依赖就绪

        默认检查: 硬件管理器存在、没有急停/中止请求
        子类可追加自己的条件（例如: 炸药是否已入槽）
        """
        if ctx.hw is None:
            return StepResult(False, "硬件管理器未初始化")
        if ctx.check_abort():
            return StepResult(False, "收到中止请求")
        return StepResult(True)

    @abstractmethod
    def execute(self, ctx: WorkflowContext) -> StepResult:
        """核心动作 — 子类必须实现（例如: 驱动电机、调用机械臂）"""

    def post_check(self, ctx: WorkflowContext) -> StepResult:
        """
        后置确认 — 动作完成后验证是否真正到位

        默认直接通过；需要确认的步骤（如电缸缩回）应覆盖此方法
        """
        return StepResult(True)

    def on_error(self, ctx: WorkflowContext, error: Optional[str] = None) -> None:
        """出错时记录，便于排查"""
        msg = error or "未知错误"
        _step_logger.error("[Step%02d] 失败: %s", self.step_index, msg)
        self.log(ctx, f"步骤失败: {msg}")

    def rollback(self, ctx: WorkflowContext) -> None:
        """失败回退 — 默认不做任何事，特殊步骤可自行实现"""
        self.log(ctx, "回滚（默认无操作）")
