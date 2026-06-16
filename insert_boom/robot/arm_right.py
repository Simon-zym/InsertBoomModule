"""
右机械臂控制器 — 固定 IP 172.16.0.88

负责:
    - 取雷管，引线经压线位和绕线器开口，放入雷管槽 (Step4)

每段动作由两段独立途径配置组成:
    ① 取/放雷管流程  ② 回初始位置流程
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from insert_boom.config_loader import get_project_root
from insert_boom.log_helper import get_logger
from insert_boom.robot.constants import RIGHT_ARM_IP, RIGHT_ARM_PORT
from insert_boom.robot.realman_api import RealmanArmAPI
from insert_boom.robot.waypoint_executor import WaypointExecutor, WaypointLoader

logger = get_logger("robot.right")

PROCESS_PICK_PLACE_DETONATOR = "process_pick_and_place_detonator"
PROCESS_RETURN_HOME = "process_return_home"


class RightArm:
    """右机械臂 — 雷管取放"""

    def __init__(self, config: dict, mode: str = "mock"):
        robot_cfg = config.get("robots", {}).get("right_arm", {})
        self.name = "right_arm"
        self.mode = mode
        self.ip = robot_cfg.get("ip", RIGHT_ARM_IP)
        self.port = int(robot_cfg.get("port", RIGHT_ARM_PORT))
        self.config_file = robot_cfg.get("config_file", "config/waypoints_right.yaml")

        gripper_cfg = config.get("hardware", {}).get("grippers", {}).get("right", {})
        self.gripper_positions: Dict[str, int] = {
            "open_position": int(gripper_cfg.get("open_position", 1000)),
            "close_detonator": int(gripper_cfg.get("close_detonator", 150)),
        }

        self.api = RealmanArmAPI(self.name, mode=mode)
        self.loader: Optional[WaypointLoader] = None
        self.executor: Optional[WaypointExecutor] = None
        self.is_connected = False

    def _resolve_config_path(self) -> str:
        path = Path(self.config_file)
        if not path.is_absolute():
            path = get_project_root() / self.config_file
        return str(path)

    def connect(self) -> Tuple[bool, str]:
        logger.info("右臂连接中 %s:%d (mode=%s)...", self.ip, self.port, self.mode)
        ok, msg = self.api.connect(self.ip, self.port)
        if ok:
            cfg_path = self._resolve_config_path()
            self.loader = WaypointLoader(cfg_path, self.gripper_positions)
            self.executor = WaypointExecutor(self.api, self.loader, self.gripper_positions)
            logger.info("右臂连接成功 %s:%d, 途径点文件: %s", self.ip, self.port, cfg_path)
        else:
            logger.error("右臂连接失败: %s", msg)
        self.is_connected = ok
        return ok, msg

    def disconnect(self) -> None:
        logger.info("右臂断开连接")
        self.api.disconnect()
        self.is_connected = False

    def move_to_home(self) -> bool:
        """直接移动到初始位置2"""
        assert self.executor is not None
        return self.executor.move_to_named_pose("home_2")

    def pick_detonator_and_place(self) -> bool:
        """
        Step4: 取雷管入槽 + 回初始
        流程1: process_pick_and_place_detonator（取雷管→经压线/绕线口→入槽）
        流程2: process_return_home（回初始位置2）
        """
        assert self.executor is not None
        logger.info("右臂 Step4: 取雷管入槽 → 回初始")
        if not self.executor.execute_process(PROCESS_PICK_PLACE_DETONATOR):
            logger.error("右臂取雷管入槽流程失败")
            return False
        if not self.executor.execute_process(PROCESS_RETURN_HOME):
            logger.error("右臂回初始流程失败")
            return False
        logger.info("右臂 Step4 全部完成")
        return True
