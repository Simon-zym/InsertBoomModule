"""
左机械臂控制器 — 固定 IP 172.16.0.89

负责:
    - 取炸药放入炸药槽 (Step2)
    - 取成品回初始 (Step13)

每段动作由两段独立途径配置组成:
    ① 取/放动作流程  ② 回初始位置流程
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from insert_boom.config_loader import get_project_root
from insert_boom.log_helper import get_logger
from insert_boom.robot.constants import LEFT_ARM_IP, LEFT_ARM_PORT
from insert_boom.robot.realman_api import RealmanArmAPI
from insert_boom.robot.waypoint_executor import WaypointExecutor, WaypointLoader

logger = get_logger("robot.left")

# waypoints_left.yaml 中的流程键名
PROCESS_PICK_PLACE_EXPLOSIVE = "process_pick_and_place_explosive"
PROCESS_RETURN_HOME = "process_return_home"
PROCESS_PICK_PRODUCT = "process_pick_product"
PROCESS_RETURN_HOME_AFTER_PRODUCT = "process_return_home_after_product"

# 左臂独立流程（与完整装配互斥，由 InsertBoomService 调度）
PROCESS_LEFT_PICK_EXPLOSIVE = "process_left_pick_explosive"
PROCESS_LEFT_MOVE_TO_TARGET = "process_left_move_to_target"


class LeftArm:
    """左机械臂 — 炸药/成品取放"""

    def __init__(self, config: dict, mode: str = "mock"):
        robot_cfg = config.get("robots", {}).get("left_arm", {})
        self.name = "left_arm"
        self.mode = mode
        self.ip = robot_cfg.get("ip", LEFT_ARM_IP)
        self.port = int(robot_cfg.get("port", LEFT_ARM_PORT))
        self.config_file = robot_cfg.get("config_file", "config/waypoints_left.yaml")

        gripper_cfg = config.get("hardware", {}).get("grippers", {}).get("left", {})
        self.gripper_positions: Dict[str, int] = {
            "open_position": int(gripper_cfg.get("open_position", 1000)),
            "close_explosive": int(gripper_cfg.get("close_explosive", 200)),
            "close_product": int(gripper_cfg.get("close_product", 250)),
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
        logger.info("左臂连接中 %s:%d (mode=%s)...", self.ip, self.port, self.mode)
        ok, msg = self.api.connect(self.ip, self.port)
        if ok:
            cfg_path = self._resolve_config_path()
            self.loader = WaypointLoader(cfg_path, self.gripper_positions)
            self.executor = WaypointExecutor(self.api, self.loader, self.gripper_positions)
            logger.info("左臂连接成功 %s:%d, 途径点文件: %s", self.ip, self.port, cfg_path)
        else:
            logger.error("左臂连接失败: %s", msg)
        self.is_connected = ok
        return ok, msg

    def disconnect(self) -> None:
        logger.info("左臂断开连接")
        self.api.disconnect()
        self.is_connected = False

    def move_to_home(self) -> bool:
        """直接移动到初始位置1"""
        assert self.executor is not None
        return self.executor.move_to_named_pose("home_1")

    def _run_processes(self, *process_keys: str) -> bool:
        """按顺序执行多段途径流程，任一失败则停止"""
        assert self.executor is not None
        for key in process_keys:
            logger.info("左臂执行流程: %s", key)
            if not self.executor.execute_process(key):
                logger.error("左臂流程 [%s] 失败，后续流程取消", key)
                return False
        return True

    def pick_explosive_and_place(self) -> bool:
        """
        Step2: 取炸药入槽 + 回初始
        流程1: process_pick_and_place_explosive（取药→入槽）
        流程2: process_return_home（回初始位置1）
        """
        logger.info("左臂 Step2: 取炸药入槽 → 回初始")
        return self._run_processes(PROCESS_PICK_PLACE_EXPLOSIVE, PROCESS_RETURN_HOME)

    def pick_product_and_return(self) -> bool:
        """
        Step13: 取成品 + 回初始
        流程1: process_pick_product（取成品）
        流程2: process_return_home_after_product（回初始位置1）
        """
        logger.info("左臂 Step13: 取成品 → 回初始")
        return self._run_processes(PROCESS_PICK_PRODUCT, PROCESS_RETURN_HOME_AFTER_PRODUCT)

    def run_pick_transfer(self) -> bool:
        """
        左臂独立流程: 取炸药 → 移至目标点

        流程1: process_left_pick_explosive — 规划路径到取药位，张夹爪取药后闭合
        流程2: process_left_move_to_target — 夹持炸药运动到配置目标点
        """
        logger.info("左臂独立流程: 取炸药 → 移至目标点")
        return self._run_processes(PROCESS_LEFT_PICK_EXPLOSIVE, PROCESS_LEFT_MOVE_TO_TARGET)
