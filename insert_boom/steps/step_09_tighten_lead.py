"""Step 9: 收紧引线(stepper_5/图标4) — 拉紧雷管引线"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step09TightenLead(StepBase):
    step_index = 9
    step_key = "step_09_tighten_lead"
    description = "收紧引线"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        stepper_cfg = ctx.system_config.get("hardware", {}).get("steppers", {}).get("stepper_5", {})

        steps = int(cfg.get("steps", stepper_cfg.get("tighten_steps", 2000)))
        speed = int(cfg.get("speed", 400))

        stepper = hw.get_stepper("stepper_5")
        self.log(ctx, f"收紧引线 stepper_5 相对运动 {steps} 步, 速度 {speed}")
        if not stepper.move_relative(steps, speed):
            return StepResult(False, "收紧引线失败")

        self.log(ctx, "引线收紧完成 ✓")
        return StepResult(True)
