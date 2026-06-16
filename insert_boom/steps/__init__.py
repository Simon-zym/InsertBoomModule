"""
装配流程全部步骤 — 按执行顺序排列

 Step | 模块                              | 做什么
------|-----------------------------------|---------------------------
  0   | step_00_self_check                | 开机自检（急停/硬件/双臂）
  1   | step_01_winder_home               | 绕线器回初始位
  2   | step_02_left_pick_explosive       | 左臂取炸药入槽→回初始
  3   | step_03_cylinder1_retract         | 电缸1缩回（给右臂让位）
  4   | step_04_right_pick_detonator      | 右臂取雷管入槽→回初始
  5   | step_05_cylinder1_extend          | 电缸1伸出夹住雷管
  6   | step_06_press_wire_position       | 压线机构(stepper_2)到位
  7   | step_07_blade_press               | 刀片(stepper_3)下压割炸药
  8   | step_08_insert_detonator          | 雷管插入(stepper_4)
  9   | step_09_tighten_lead              | 收紧引线(stepper_5)
 10   | step_10_wrap_film                 | 绕线器(stepper_1)缠保鲜膜
 11   | step_11_cylinder2_cut             | 电缸2切割保鲜膜
 12   | step_12_press_wire_home           | 压线机构(stepper_2)回初始
 13   | step_13_left_pick_product         | 左臂取成品→回初始
"""

from insert_boom.steps.step_00_self_check import Step00SelfCheck
from insert_boom.steps.step_01_winder_home import Step01WinderHome
from insert_boom.steps.step_02_left_pick_explosive import Step02LeftPickExplosive
from insert_boom.steps.step_03_cylinder1_retract import Step03Cylinder1Retract
from insert_boom.steps.step_04_right_pick_detonator import Step04RightPickDetonator
from insert_boom.steps.step_05_cylinder1_extend import Step05Cylinder1Extend
from insert_boom.steps.step_06_press_wire_position import Step06PressWirePosition
from insert_boom.steps.step_07_blade_press import Step07BladePress
from insert_boom.steps.step_08_insert_detonator import Step08InsertDetonator
from insert_boom.steps.step_09_tighten_lead import Step09TightenLead
from insert_boom.steps.step_10_wrap_film import Step10WrapFilm
from insert_boom.steps.step_11_cylinder2_cut import Step11Cylinder2Cut
from insert_boom.steps.step_12_press_wire_home import Step12PressWireHome
from insert_boom.steps.step_13_left_pick_product import Step13LeftPickProduct

ALL_STEPS = [
    Step00SelfCheck,
    Step01WinderHome,
    Step02LeftPickExplosive,
    Step03Cylinder1Retract,
    Step04RightPickDetonator,
    Step05Cylinder1Extend,
    Step06PressWirePosition,
    Step07BladePress,
    Step08InsertDetonator,
    Step09TightenLead,
    Step10WrapFilm,
    Step11Cylinder2Cut,
    Step12PressWireHome,
    Step13LeftPickProduct,
]

__all__ = ["ALL_STEPS"]
