"""Step 11: 电缸2伸出切割保鲜膜，然后缩回"""

import time

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step11Cylinder2Cut(StepBase):
    step_index = 11
    step_key = "step_11_cut_film"
    description = "电缸2切割保鲜膜"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        timeout = float(cfg.get("timeout", 3.0))
        hold_time = float(cfg.get("cut_hold_time", 1.0))

        cyl = hw.get_cylinder("cylinder_2")
        self.log(ctx, f"电缸2伸出切割 (超时 {timeout}s)...")
        if not cyl.extend(timeout=timeout):
            return StepResult(False, "电缸2伸出失败")

        if hold_time > 0:
            self.log(ctx, f"保持切割 {hold_time}s...")
            time.sleep(hold_time)

        self.log(ctx, "电缸2缩回...")
        if not cyl.retract(timeout=timeout):
            return StepResult(False, "电缸2缩回失败")

        self.log(ctx, "保鲜膜切割完成 ✓")
        return StepResult(True)

    def post_check(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        if not hw.get_cylinder("cylinder_2").is_retracted():
            return StepResult(False, "电缸2未缩回到位")
        return StepResult(True)
