"""
完整装配流程 — 封装现有 Step0~Step13
"""

from __future__ import annotations

from insert_boom.core.context import WorkflowContext
from insert_boom.core.flow_types import FlowType, RunResult
from insert_boom.core.workflow_engine import WorkflowEngine
from insert_boom.log_helper import get_logger
from insert_boom.steps import ALL_STEPS

logger = get_logger("flow.assembly")


def run_assembly_flow(ctx: WorkflowContext, start_from: int = 0) -> RunResult:
    """执行完整装配流程"""
    logger.info("启动装配流程 (start_from=%d)", start_from)
    engine = WorkflowEngine.from_step_classes(ctx, ALL_STEPS)
    result = engine.run(start_from=start_from)

    return RunResult(
        success=result.success,
        flow_type=FlowType.ASSEMBLY.value,
        message=result.message,
        failed_step=result.failed_step,
    )
