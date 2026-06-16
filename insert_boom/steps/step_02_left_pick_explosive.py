"""
Step 2: 左臂取炸药放入炸药槽，然后回初始

设备: 左机械臂 172.16.0.89 + 左夹爪

两段独立途径配置（waypoints_left.yaml）:
    ① process_pick_and_place_explosive — 到取药位→夹炸药→途径点入槽
    ② process_return_home             — 放完后回初始位置1
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step02LeftPickExplosive(StepBase):
    step_index = 2
    step_key = "step_02_left_pick_explosive"
    description = "左臂取炸药入槽并回初始"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if not ctx.winder_at_home:
            return StepResult(False, "绕线器未在初始位，请先完成 Step1")
        if ctx.left_arm is None:
            return StepResult(False, "左机械臂未初始化")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        assert ctx.left_arm is not None
        self.log(ctx, "开始: 取炸药入槽 → 回初始（两段途径配置）")
        if not ctx.left_arm.pick_explosive_and_place():
            return StepResult(False, "左臂取炸药入槽或回初始失败")

        ctx.explosive_in_slot = True
        self.log(ctx, "炸药已入槽，左臂已回初始 ✓")
        return StepResult(True)
