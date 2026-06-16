"""
Step 5: 电缸1伸出，夹住雷管

前提: Step4 雷管已放入槽中
设备: 电缸1
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step05Cylinder1Extend(StepBase):
    step_index = 5
    step_key = "step_05_cylinder1_extend"
    description = "电缸1伸出夹雷管"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if not ctx.detonator_in_slot:
            return StepResult(False, "雷管尚未放入槽中，请先完成 Step4")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        timeout = float(cfg.get("timeout", 5.0))

        cyl = hw.get_cylinder("cylinder_1")
        self.log(ctx, f"电缸1伸出夹住雷管 (超时 {timeout}s)...")
        if not cyl.extend(timeout=timeout):
            return StepResult(False, "电缸1伸出失败")

        ctx.detonator_clamped = True
        self.log(ctx, "电缸1已伸出，雷管已夹住")
        return StepResult(True)

    def post_check(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        if not hw.get_cylinder("cylinder_1").is_extended():
            return StepResult(False, "电缸1未确认伸出到位")
        self.log(ctx, "电缸1伸出到位确认 ✓")
        return StepResult(True)
