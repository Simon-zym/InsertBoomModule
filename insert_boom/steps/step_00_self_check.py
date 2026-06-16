"""
Step 0: 系统自检 — 开工前确认一切正常

检查项:
    1. 急停按钮没被按下
    2. 硬件（步进/电缸/传感器）已连接
    3. 左臂 172.16.0.89 已连接
    4. 右臂 172.16.0.88 已连接
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult
from insert_boom.robot.constants import LEFT_ARM_IP, RIGHT_ARM_IP


class Step00SelfCheck(StepBase):
    step_index = 0
    step_key = "step_00_self_check"
    description = "系统自检"

    def execute(self, ctx: WorkflowContext) -> StepResult:
        hw = ctx.hw
        assert hw is not None

        # 1. 急停
        self.log(ctx, "检查急停按钮...")
        if not hw.check_emergency():
            return StepResult(False, "急停已按下，请先复位急停按钮")

        # 2. 硬件
        self.log(ctx, f"检查硬件连接 (mode={hw.mode})...")
        if not hw._connected:
            return StepResult(False, "硬件未连接，请检查串口")

        # 3. 左臂
        self.log(ctx, f"检查左机械臂 ({LEFT_ARM_IP})...")
        if ctx.left_arm is None or not ctx.left_arm.is_connected:
            return StepResult(False, f"左机械臂未连接 ({LEFT_ARM_IP})")

        # 4. 右臂
        self.log(ctx, f"检查右机械臂 ({RIGHT_ARM_IP})...")
        if ctx.right_arm is None or not ctx.right_arm.is_connected:
            return StepResult(False, f"右机械臂未连接 ({RIGHT_ARM_IP})")

        self.log(ctx, "系统自检全部通过 ✓")
        return StepResult(True)
