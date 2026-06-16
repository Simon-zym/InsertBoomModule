"""
Step 4: 右臂取雷管入槽，然后回初始

设备: 右机械臂 172.16.0.88 + 右夹爪

两段独立途径配置（waypoints_right.yaml）:
    ① process_pick_and_place_detonator — 取雷管→经压线位→绕线器开口→入槽
    ② process_return_home              — 放完后回初始位置2
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step04RightPickDetonator(StepBase):
    step_index = 4
    step_key = "step_04_right_pick_detonator"
    description = "右臂取雷管入槽并回初始"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        hw = ctx.hw
        assert hw is not None
        if not hw.get_cylinder("cylinder_1").is_retracted():
            return StepResult(False, "电缸1未缩回，右臂无法操作")
        if ctx.right_arm is None:
            return StepResult(False, "右机械臂未初始化")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        assert ctx.right_arm is not None
        self.log(ctx, "开始: 取雷管入槽 → 回初始（两段途径配置）")
        if not ctx.right_arm.pick_detonator_and_place():
            return StepResult(False, "右臂取雷管入槽或回初始失败")

        ctx.detonator_in_slot = True
        self.log(ctx, "雷管已入槽，右臂已回初始 ✓")
        return StepResult(True)
