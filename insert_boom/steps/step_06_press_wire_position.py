"""Step 6: 压线机构(stepper_2/图标5)运动到压线位置"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step06PressWirePosition(StepBase):
    step_index = 6
    step_key = "step_06_press_wire"
    description = "压线机构到位"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if not ctx.detonator_clamped:
            return StepResult(False, "雷管尚未被电缸1夹住，请先完成 Step5")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)
        stepper_cfg = ctx.system_config.get("hardware", {}).get("steppers", {}).get("stepper_2", {})

        position = int(cfg.get("position", stepper_cfg.get("press_position", 5000)))
        speed = int(cfg.get("speed", 300))
        timeout = float(cfg.get("timeout", 10.0))

        stepper = hw.get_stepper("stepper_2")
        self.log(ctx, f"压线机构 stepper_2 → 位置 {position}, 速度 {speed}")
        if not stepper.move_to_position(position, speed, timeout=timeout):
            return StepResult(False, "压线机构运动失败")

        sensor_name = cfg.get("ready_sensor")
        if sensor_name and sensor_name in hw.sensors:
            timeout_s = float(cfg.get("sensor_timeout", 5.0))
            self.log(ctx, f"等待压线到位传感器 [{sensor_name}]...")
            if not hw.get_sensor(sensor_name).wait_for(True, timeout=timeout_s):
                return StepResult(False, "压线到位传感器超时")

        self.log(ctx, "压线机构已到位 ✓")
        return StepResult(True)
