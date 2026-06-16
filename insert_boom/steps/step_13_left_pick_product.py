"""
Step 13: 左臂取成品，回初始 — 装配流程最后一步

设备: 左机械臂 172.16.0.89

两段独立途径配置:
    ① process_pick_product              — 到成品位→夹取
    ② process_return_home_after_product — 回初始位置1
"""

from insert_boom.core.context import WorkflowContext
from insert_boom.core.step_base import StepBase, StepResult


class Step13LeftPickProduct(StepBase):
    step_index = 13
    step_key = "step_13_left_pick_product"
    description = "左臂取成品回初始"

    def pre_check(self, ctx: WorkflowContext) -> StepResult:
        base = super().pre_check(ctx)
        if not base.success:
            return base
        if ctx.left_arm is None:
            return StepResult(False, "左机械臂未初始化")
        return StepResult(True)

    def execute(self, ctx: WorkflowContext) -> StepResult:
        assert ctx.left_arm is not None
        self.log(ctx, "开始: 取成品 → 回初始（最后一步）")
        if not ctx.left_arm.pick_product_and_return():
            return StepResult(False, "左臂取成品或回初始失败")

        ctx.product_picked = True
        self.log(ctx, "成品已取回，装配流程全部完成 ✓")
        return StepResult(True)
