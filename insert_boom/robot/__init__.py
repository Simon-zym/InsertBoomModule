"""Robot 模块导出"""

from insert_boom.robot.arm_left import LeftArm
from insert_boom.robot.arm_right import RightArm
from insert_boom.robot.realman_api import RealmanArmAPI
from insert_boom.robot.waypoint_executor import WaypointExecutor, WaypointLoader

__all__ = ["LeftArm", "RightArm", "RealmanArmAPI", "WaypointExecutor", "WaypointLoader"]
