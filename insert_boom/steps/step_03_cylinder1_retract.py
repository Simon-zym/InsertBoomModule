"""
Step 3: 电缸1缩回

为什么: 左臂放完炸药后，电缸1需要缩回给右臂操作让出空间
设备: 电缸1（RS485 独立串口）
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step03Cylinder1Retract(StepBase):
    step_index = 3
    step_key = "step_03_cylinder1_retract"
    description = "电缸1缩回"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if not ctx.explosive_in_slot:
            return StepResult(False, "炸药尚未放入槽中，请先完成 Step2")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        timeout = float(cfg.get("timeout", 5.0))

        cyl = hw.get_cylinder("cylinder_1")
        self.log(ctx, f"电缸1缩回 (超时 {timeout}s)...")
        if not cyl.retract(timeout=timeout):
            return StepResult(False, "电缸1缩回失败")
        self.log(ctx, "电缸1缩回完成")
        return StepResult(True)

    def post_check(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        if not hw.get_cylinder("cylinder_1").is_retracted():
            return StepResult(False, "电缸1未确认缩回到位")
        self.log(ctx, "电缸1缩回到位确认 ✓")
        return StepResult(True)
