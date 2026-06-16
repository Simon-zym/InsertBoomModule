"""Step 12: 压线机构(stepper_2/图标5)回到初始位置"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step12PressWireHome(StepBase):
    step_index = 12
    step_key = "step_12_press_wire_home"
    description = "压线机构回初始"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        speed = int(cfg.get("speed", 300))

        stepper = hw.get_stepper("stepper_2")
        self.log(ctx, f"压线机构 stepper_2 回初始, 速度 {speed}")
        if not stepper.move_to_home(speed=speed):
            return StepResult(False, "压线机构回初始失败")

        self.log(ctx, "压线机构已回初始 ✓")
        return StepResult(True)
