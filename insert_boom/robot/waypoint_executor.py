"""
途径点执行器 — 读取 YAML 配置，驱动机械臂逐点运动

两类配置:
    命名位姿 (如 home_1)  — 单个位置，直接移动过去
    运动流程 (如 process_pick_and_place_explosive) — 多个途径点组成的完整动作

每个途径点可以附带夹爪动作 (gripper_action):
    close_explosive  — 夹紧炸药
    open             — 松开夹爪
    等等...
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

from insert_boom.log_helper import get_logger
from insert_boom.robot.realman_api import RealmanArmAPI

logger = get_logger("robot.waypoint")


def euler_to_quaternion(
    roll: float, pitch: float, yaw: float
) -> tuple[float, float, float, float]:
    """把欧拉角 (roll, pitch, yaw) 转成机械臂需要的四元数"""
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    w = cr * cp * cy + sr * sp * sy
    return x, y, z, w


@dataclass
class Waypoint:
    """单个途径点 — 机械臂要到达的一个位置"""

    name: str
    pos_x: float
    pos_y: float
    pos_z: float
    roll: float
    pitch: float
    yaw: float
    speed: int = 20
    block: bool = True
    trajectory_connect: int = 0
    gripper_action: Optional[str] = None


@dataclass
class MotionProcess:
    """一组途径点组成的完整动作流程"""

    key: str
    name: str
    description: str
    waypoints: List[Waypoint] = field(default_factory=list)


@dataclass
class NamedPose:
    """命名位姿 — 如 home_1 表示"初始位置1" """

    name: str
    pos_x: float
    pos_y: float
    pos_z: float
    roll: float
    pitch: float
    yaw: float
    speed: int = 20


class WaypointLoader:
    """从 YAML 文件加载途径点和命名位姿"""

    def __init__(self, config_file: str, gripper_positions: Optional[Dict[str, int]] = None):
        self.config_file = config_file
        self.gripper_positions = gripper_positions or {}
        self.processes: Dict[str, MotionProcess] = {}
        self.named_poses: Dict[str, NamedPose] = {}
        self._load()

    def _load(self) -> None:
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        for key, data in config.items():
            if not isinstance(data, dict):
                continue

            if "waypoints" in data:
                process = MotionProcess(
                    key=key,
                    name=data.get("name", key),
                    description=data.get("description", ""),
                )
                for wp_node in data["waypoints"]:
                    process.waypoints.append(self._parse_waypoint(wp_node))
                self.processes[key] = process
            elif "position" in data:
                self.named_poses[key] = NamedPose(
                    name=key,
                    pos_x=float(data["position"]["x"]),
                    pos_y=float(data["position"]["y"]),
                    pos_z=float(data["position"]["z"]),
                    roll=float(data.get("euler", {}).get("roll", 0)),
                    pitch=float(data.get("euler", {}).get("pitch", 0)),
                    yaw=float(data.get("euler", {}).get("yaw", 0)),
                    speed=int(data.get("speed", 20)),
                )

        logger.info(
            "途径点加载完成: %s — %d 个流程, %d 个命名位姿",
            self.config_file,
            len(self.processes),
            len(self.named_poses),
        )
        for pk, proc in self.processes.items():
            logger.debug("  流程 %s: %s (%d 点)", pk, proc.description, len(proc.waypoints))

    def _parse_waypoint(self, node: dict) -> Waypoint:
        return Waypoint(
            name=node.get("name", ""),
            pos_x=float(node["position"]["x"]),
            pos_y=float(node["position"]["y"]),
            pos_z=float(node["position"]["z"]),
            roll=float(node.get("euler", {}).get("roll", 0)),
            pitch=float(node.get("euler", {}).get("pitch", 0)),
            yaw=float(node.get("euler", {}).get("yaw", 0)),
            speed=int(node.get("speed", 20)),
            block=bool(node.get("block", True)),
            trajectory_connect=int(node.get("trajectory_connect", 0)),
            gripper_action=node.get("gripper_action"),
        )


class WaypointExecutor:
    """执行途径点 — 按顺序驱动机械臂运动和夹爪"""

    GRIPPER_ACTION_MAP = {
        "open": "open_position",
        "close": "close_position",
        "close_explosive": "close_explosive",
        "close_detonator": "close_detonator",
        "close_product": "close_product",
    }

    def __init__(
        self,
        api: RealmanArmAPI,
        loader: WaypointLoader,
        default_gripper: Optional[Dict[str, int]] = None,
    ):
        self.api = api
        self.loader = loader
        self.default_gripper = default_gripper or {"open_position": 1000}

    def move_to_named_pose(self, pose_name: str) -> bool:
        """移动到某个命名位置（如 home_1）"""
        pose = self.loader.named_poses.get(pose_name)
        if pose is None:
            logger.error("找不到命名位姿: %s", pose_name)
            return False

        logger.info("移动到 [%s] (%.3f, %.3f, %.3f) speed=%d",
                      pose_name, pose.pos_x, pose.pos_y, pose.pos_z, pose.speed)
        result, msg = self.api.movej_p(
            pose.pos_x, pose.pos_y, pose.pos_z,
            pose.roll, pose.pitch, pose.yaw,
            speed=pose.speed, block=True,
        )
        if result != 0:
            logger.error("移动到 %s 失败: %s", pose_name, msg)
        return result == 0

    def execute_process(self, process_key: str) -> bool:
        """执行一整段途径点流程（如: 取炸药入槽）"""
        process = self.loader.processes.get(process_key)
        if process is None:
            logger.error("找不到运动流程: %s", process_key)
            return False

        total = len(process.waypoints)
        logger.info("▶ 开始流程 [%s]: %s（共 %d 个途径点）",
                     process_key, process.description, total)

        for i, wp in enumerate(process.waypoints):
            logger.info("  途径点 %d/%d [%s] → (%.3f, %.3f, %.3f) speed=%d",
                        i + 1, total, wp.name, wp.pos_x, wp.pos_y, wp.pos_z, wp.speed)

            # 如果该点需要操作夹爪，先执行夹爪动作
            if wp.gripper_action and wp.gripper_action != "none":
                if not self._do_gripper_action(wp.name, wp.gripper_action):
                    return False

            result, msg = self.api.movej_p(
                wp.pos_x, wp.pos_y, wp.pos_z,
                wp.roll, wp.pitch, wp.yaw,
                speed=wp.speed,
                block=wp.block,
                trajectory_connect=wp.trajectory_connect,
            )
            if result != 0:
                logger.error("  途径点 [%s] 运动失败: %s", wp.name, msg)
                return False

        logger.info("✓ 流程 [%s] 完成", process_key)
        return True

    def _do_gripper_action(self, waypoint_name: str, action: str) -> bool:
        """执行夹爪开合"""
        key = self.GRIPPER_ACTION_MAP.get(action, action)
        position = self.default_gripper.get(key)
        if position is None:
            logger.warning("途径点 [%s] 夹爪动作 '%s' 未配置，跳过", waypoint_name, action)
            return True

        logger.info("  夹爪动作: %s → 位置 %d", action, position)
        result, msg = self.api.set_gripper_position(position, block=True)
        if result != 0:
            logger.error("  夹爪动作 %s 失败: %s", action, msg)
        return result == 0
