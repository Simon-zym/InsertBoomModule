"""Step 8: 雷管插入(stepper_4/图标3) — 将雷管推入炸药"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step08InsertDetonator(StepBase):
    step_index = 8
    step_key = "step_08_insert_detonator"
    description = "雷管插入炸药"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        stepper_cfg = ctx.system_config.get("hardware", {}).get("steppers", {}).get("stepper_4", {})

        position = int(cfg.get("position", stepper_cfg.get("insert_position", 8000)))
        speed = int(cfg.get("speed", 200))

        stepper = hw.get_stepper("stepper_4")
        self.log(ctx, f"雷管插入 stepper_4 → 位置 {position}, 速度 {speed}")
        if not stepper.move_to_position(position, speed):
            return StepResult(False, "雷管插入运动失败")

        self.log(ctx, "雷管插入完成 ✓")
        return StepResult(True)
