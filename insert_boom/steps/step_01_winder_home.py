"""
Step 1: 绕线器回初始位

设备: 步进电机1（图标1, RS485）+ 绕线器遮挡传感器

逻辑（通俗版）:
    看传感器 → 没遮挡 = 已经在初始位 → 不用动
              → 有遮挡 = 不在初始位 → 让步进电机1回零 → 等到没遮挡
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step01WinderHome(StepBase):
    step_index = 1
    step_key = "step_01_winder_home"
    description = "绕线器回初始位"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        cfg = ctx.get_step_config(self.step_key)

        sensor = hw.get_sensor("winder_home")
        stepper = hw.get_stepper("stepper_1")
        speed = int(cfg.get("speed", 500))
        timeout = float(cfg.get("sensor_timeout", 10.0))

        blocked = sensor.read()
        self.log(ctx, f"绕线器传感器状态: {'遮挡(不在初始位)' if blocked else '未遮挡(在初始位)'}")

        if not blocked:
            self.log(ctx, "已在初始位，无需运动")
            ctx.winder_at_home = True
            return StepResult(True)

        # 传感器遮挡 → 需要回零
        self.log(ctx, f"开始回零 (stepper_1, speed={speed})...")
        if not stepper.move_to_home(speed=speed, timeout=timeout):
            return StepResult(False, "绕线器回零运动失败")

        # Mock 模式下自动模拟传感器变为未遮挡
        if hasattr(hw, "simulate_winder_reached_home"):
            hw.simulate_winder_reached_home()

        self.log(ctx, f"等待传感器变为未遮挡 (超时 {timeout}s)...")
        if not sensor.wait_for(False, timeout=timeout):
            return StepResult(False, f"等待绕线器初始位超时 ({timeout}s)")

        ctx.winder_at_home = True
        self.log(ctx, "绕线器已到达初始位置 ✓")
        return StepResult(True)

    def post_check(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None
        if hw.get_sensor("winder_home").read():
            return StepResult(False, "传感器仍显示遮挡，绕线器可能未到位")
        if not ctx.winder_at_home:
            return StepResult(False, "绕线器初始位标志未置位")
        return StepResult(True)
