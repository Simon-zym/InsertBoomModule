"""Step 7: 刀片(stepper_3/图标2)下压，割破炸药外皮"""

import time

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step07BladePress(StepBase):
    step_index = 7
    step_key = "step_07_blade_press"
    description = "刀片下压割炸药"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        stepper_cfg = ctx.system_config.get("hardware", {}).get("steppers", {}).get("stepper_3", {})

        position = int(cfg.get("position", stepper_cfg.get("press_position", 3000)))
        speed = int(cfg.get("speed", 200))
        hold_time = float(cfg.get("hold_time", 0.5))

        stepper = hw.get_stepper("stepper_3")
        self.log(ctx, f"刀片 stepper_3 下压 → 位置 {position}, 速度 {speed}")
        if not stepper.move_to_position(position, speed):
            return StepResult(False, "刀片下压失败")

        if hold_time > 0:
            self.log(ctx, f"保持下压 {hold_time}s...")
            time.sleep(hold_time)

        self.log(ctx, "刀片下压完成 ✓")
        return StepResult(True)
