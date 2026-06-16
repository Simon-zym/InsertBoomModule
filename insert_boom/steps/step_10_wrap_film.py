"""Step 10: 绕线器(stepper_1/图标1)缠绕保鲜膜"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step10WrapFilm(StepBase):
    step_index = 10
    step_key = "step_10_wrap_film"
    description = "缠绕保鲜膜"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if not ctx.winder_at_home:
            return StepResult(False, "绕线器初始位状态异常")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)

        wrap_steps = int(cfg.get("wrap_steps", 10000))
        speed = int(cfg.get("speed", 300))

        stepper = hw.get_stepper("stepper_1")
        self.log(ctx, f"绕线器 stepper_1 缠绕 {wrap_steps} 步, 速度 {speed}")
        if not stepper.move_relative(wrap_steps, speed):
            return StepResult(False, "缠绕保鲜膜失败")

        self.log(ctx, "保鲜膜缠绕完成 ✓")
        return StepResult(True)
