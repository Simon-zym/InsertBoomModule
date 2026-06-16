"""
流程引擎 — 按顺序执行 Step0 ~ Step13

职责:
    - 逐步调用每个步骤的 pre_check → execute → post_check
    - 失败时按 workflow.yaml 配置重试
    - 通过事件通知界面/控制台当前进度
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Type

from insert_boom.core.context import WorkflowContext
from insert_boom.core.events import EventType, WorkflowEvent, WorkflowState
from insert_boom.core.step_base import StepBase, StepResult
from insert_boom.log_helper import get_logger

logger = get_logger("engine")


@dataclass
class WorkflowResult:
    """全流程最终结果"""

    success: bool
    message: str = ""
    failed_step: int = -1


class WorkflowEngine:
    """
    装配流程调度器

    示例:
        engine = WorkflowEngine.from_step_classes(ctx, ALL_STEPS)
        result = engine.run()
    """

    def __init__(self, ctx: WorkflowContext, steps: List[StepBase]):
        self.ctx = ctx
        self.steps = steps
        wf = ctx.workflow_config.get("workflow", {})
        self.max_retries = int(wf.get("max_retries", 2))
        self.retry_delay = float(wf.get("retry_delay_sec", 1.0))
        self.step_timeout = float(wf.get("step_timeout", 60.0))
        logger.info(
            "流程引擎就绪: 共 %d 步, 最大重试 %d 次",
            len(steps),
            self.max_retries,
        )

    @classmethod
    def from_step_classes(
        cls, ctx: WorkflowContext, step_classes: List[Type[StepBase]]
    ) -> "WorkflowEngine":
        return cls(ctx, [step_cls() for step_cls in step_classes])

    def run(self, start_from: int = 0) -> WorkflowResult:
        """从头到尾执行所有步骤（可从中间某步开始，方便调试）"""
        self.ctx.state = WorkflowState.RUNNING
        self.ctx.abort_requested = False

        if start_from > 0:
            logger.info("调试模式: 从 Step %d 开始执行", start_from)

        self.ctx.emit(
            WorkflowEvent(event_type=EventType.WORKFLOW_STARTED, message="装配流程开始")
        )
        logger.info(">>> 装配流程开始 <<<")

        for step in self.steps:
            if step.step_index < start_from:
                continue

            if self.ctx.check_abort():
                return self._abort(step.step_index)

            self.ctx.current_step = step.step_index
            self.ctx.emit(
                WorkflowEvent(
                    event_type=EventType.STEP_STARTED,
                    message=step.description,
                    step_index=step.step_index,
                    step_name=step.step_key,
                )
            )
            logger.info("--- Step %02d: %s ---", step.step_index, step.description)

            result = self._run_single_step(step)
            if not result.success:
                self.ctx.state = WorkflowState.ERROR
                logger.error("Step %02d 失败: %s", step.step_index, result.message)
                self.ctx.emit(
                    WorkflowEvent(
                        event_type=EventType.STEP_FAILED,
                        message=result.message,
                        step_index=step.step_index,
                        step_name=step.step_key,
                    )
                )
                self.ctx.emit(
                    WorkflowEvent(
                        event_type=EventType.WORKFLOW_ERROR,
                        message=result.message,
                        step_index=step.step_index,
                    )
                )
                return WorkflowResult(False, result.message, step.step_index)

            logger.info("Step %02d 完成", step.step_index)
            self.ctx.emit(
                WorkflowEvent(
                    event_type=EventType.STEP_COMPLETED,
                    message=f"Step {step.step_index} 完成",
                    step_index=step.step_index,
                    step_name=step.step_key,
                )
            )

        self.ctx.state = WorkflowState.COMPLETED
        logger.info(">>> 装配流程全部完成 <<<")
        self.ctx.emit(
            WorkflowEvent(event_type=EventType.WORKFLOW_COMPLETED, message="装配流程全部完成")
        )
        return WorkflowResult(True, "流程完成")

    def _run_single_step(self, step: StepBase) -> StepResult:
        """执行单步: 前置检查 → 执行(可重试) → 后置确认"""

        # ---- 1. 前置检查 ----
        logger.debug("Step %02d 前置检查...", step.step_index)
        pre = step.pre_check(self.ctx)
        if not pre.success:
            step.on_error(self.ctx, f"前置检查未通过: {pre.message}")
            return pre
        logger.debug("Step %02d 前置检查通过", step.step_index)

        # ---- 2. 执行（失败可重试）----
        last_error = ""
        max_attempts = self.max_retries + 1
        for attempt in range(1, max_attempts + 1):
            if self.ctx.check_abort():
                return StepResult(False, "流程被中止")

            if attempt > 1:
                logger.warning(
                    "Step %02d 第 %d/%d 次重试，%ds 后重试...",
                    step.step_index,
                    attempt,
                    max_attempts,
                    int(self.retry_delay),
                )
                step.log(self.ctx, f"第 {attempt} 次重试...")
                time.sleep(self.retry_delay)

            logger.info("Step %02d 开始执行...", step.step_index)
            exe = step.execute(self.ctx)
            if not exe.success:
                last_error = exe.message
                step.on_error(self.ctx, exe.message)
                continue

            # ---- 3. 后置确认 ----
            logger.debug("Step %02d 后置确认...", step.step_index)
            post = step.post_check(self.ctx)
            if not post.success:
                last_error = post.message
                step.on_error(self.ctx, f"后置确认未通过: {post.message}")
                continue

            step.log(self.ctx, "步骤完成 ✓")
            return StepResult(True)

        # 所有重试用尽
        if self.ctx.workflow_config.get("workflow", {}).get("auto_rollback", False):
            logger.warning("Step %02d 触发回滚", step.step_index)
            step.rollback(self.ctx)

        return StepResult(False, last_error or "步骤执行失败")

    def _abort(self, step_index: int) -> WorkflowResult:
        self.ctx.state = WorkflowState.ABORTED
        msg = f"流程在 Step {step_index} 被中止"
        logger.warning(msg)
        self.ctx.emit(
            WorkflowEvent(
                event_type=EventType.WORKFLOW_ABORTED,
                message=msg,
                step_index=step_index,
            )
        )
        return WorkflowResult(False, msg, step_index)

    def stop(self) -> None:
        """外部急停入口"""
        logger.warning("收到停止请求")
        self.ctx.request_abort()
