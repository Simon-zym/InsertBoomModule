"""
左臂独立流程 — 取炸药并移至目标点

两段独立途径配置（waypoints_left.yaml）:
    process_left_pick_explosive  — 规划路径到取药位，张夹爪取药后闭合
    process_left_move_to_target  — 夹持炸药运动到目标点

与完整装配流程互斥，同一时刻只能执行一种。
"""

from __future__ import annotations

from insert_boom.core.context import WorkflowContext
from insert_boom.core.flow_types import FlowType, RunResult
from insert_boom.core.events import EventType, WorkflowEvent, WorkflowState
from insert_boom.log_helper import get_logger
from insert_boom.robot.arm_left import (
    PROCESS_LEFT_MOVE_TO_TARGET,
    PROCESS_LEFT_PICK_EXPLOSIVE,
)

logger = get_logger("flow.left_pick")


def run_left_pick_transfer_flow(ctx: WorkflowContext) -> RunResult:
    """执行左臂取炸药 → 移至目标点"""
    if ctx.left_arm is None or not ctx.left_arm.is_connected:
        return RunResult(
            success=False,
            flow_type=FlowType.LEFT_PICK_TRANSFER.value,
            message="左机械臂未连接",
        )

    ctx.state = WorkflowState.RUNNING
    ctx.emit(
        WorkflowEvent(
            event_type=EventType.WORKFLOW_STARTED,
            message="左臂取炸药并移至目标点",
        )
    )
    logger.info(">>> 左臂独立流程开始 <<<")

    try:
        if not ctx.left_arm.run_pick_transfer():
            ctx.state = WorkflowState.ERROR
            msg = "左臂取炸药或移至目标点失败"
            logger.error(msg)
            ctx.emit(WorkflowEvent(event_type=EventType.WORKFLOW_ERROR, message=msg))
            return RunResult(False, FlowType.LEFT_PICK_TRANSFER.value, msg)

        ctx.state = WorkflowState.COMPLETED
        msg = "左臂取炸药并移至目标点完成"
        logger.info(">>> %s <<<", msg)
        ctx.emit(WorkflowEvent(event_type=EventType.WORKFLOW_COMPLETED, message=msg))
        return RunResult(True, FlowType.LEFT_PICK_TRANSFER.value, msg)

    except Exception as exc:
        ctx.state = WorkflowState.ERROR
        msg = f"左臂独立流程异常: {exc}"
        logger.exception(msg)
        return RunResult(False, FlowType.LEFT_PICK_TRANSFER.value, msg)
