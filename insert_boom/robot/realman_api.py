"""
睿尔曼机械臂 Python SDK 封装

从 TestRealmanCanFD1.py 的 RoboticArmAPI 提取并扩展，
支持 movej、movej_canfd、夹爪、途径点序列。
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple

logger = logging.getLogger("insert_boom.robot.realman")

try:
    from Robotic_Arm.rm_robot_interface import RoboticArm, rm_thread_mode_e

    RM_API_AVAILABLE = True
except ImportError:
    RM_API_AVAILABLE = False
    RoboticArm = None  # type: ignore
    rm_thread_mode_e = None  # type: ignore

JOINT_COUNT = 7
GRIPPER_POSITION_MAX = 1000


class RealmanArmAPI:
    """
    单臂 RealMan API 封装

    mode:
        mock  — 不连接真实臂，打印日志模拟
        real  — 使用 Robotic_Arm SDK
    """

    def __init__(self, name: str = "arm", mode: str = "mock"):
        self.name = name
        self.mode = mode
        self.arm = None
        self.handle = None
        self.is_connected = False
        self._mock_joints = [0.0] * JOINT_COUNT

    def connect(self, ip: str = "172.16.0.88", port: int = 8080) -> Tuple[bool, str]:
        if self.mode == "mock":
            self.is_connected = True
            msg = f"[Mock] {self.name} 已连接 ({ip}:{port})"
            logger.info(msg)
            return True, msg

        if not RM_API_AVAILABLE:
            return False, "Robotic_Arm SDK 未安装"

        try:
            self.arm = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E)
            self.handle = self.arm.rm_create_robot_arm(ip, port)
            if self.handle is not None and hasattr(self.handle, "id") and self.handle.id != -1:
                self.is_connected = True
                return True, f"{self.name} 连接成功，ID: {self.handle.id}"
            return False, f"{self.name} 连接失败"
        except Exception as exc:
            return False, f"{self.name} 连接异常: {exc}"

    def disconnect(self) -> None:
        if self.mode == "real" and self.arm and self.handle:
            try:
                self.arm.rm_delete_robot_arm()
            except Exception:
                pass
        self.is_connected = False
        self.arm = None
        self.handle = None

    def movej(self, joints: List[float], speed: int = 20, block: bool = True) -> Tuple[int, str]:
        """关节空间运动 MoveJ"""
        if not self.is_connected:
            return -1, "未连接"

        joints_float = [float(j) for j in (joints + [0.0] * JOINT_COUNT)[:JOINT_COUNT]]

        if self.mode == "mock":
            logger.info("[Mock:%s] movej %s speed=%d", self.name, joints_float, speed)
            self._mock_joints = joints_float
            time.sleep(0.5)
            return 0, "成功"

        try:
            result = self.arm.rm_movej(joints_float, speed, 0, 0, 1)
            if block and result == 0:
                time.sleep(2.0)
            return result, "成功" if result == 0 else f"失败，错误码: {result}"
        except Exception as exc:
            return -1, f"异常: {exc}"

    def movej_p(
        self,
        x: float,
        y: float,
        z: float,
        roll: float,
        pitch: float,
        yaw: float,
        speed: int = 20,
        block: bool = True,
        trajectory_connect: int = 0,
    ) -> Tuple[int, str]:
        """笛卡尔空间运动 MoveJ_P"""
        if not self.is_connected:
            return -1, "未连接"

        if self.mode == "mock":
            logger.info(
                "[Mock:%s] movej_p (%.3f,%.3f,%.3f) euler(%.2f,%.2f,%.2f) speed=%d",
                self.name,
                x,
                y,
                z,
                roll,
                pitch,
                yaw,
                speed,
            )
            time.sleep(0.3)
            return 0, "成功"

        try:
            from insert_boom.robot.waypoint_executor import euler_to_quaternion

            qx, qy, qz, qw = euler_to_quaternion(roll, pitch, yaw)
            pose = [x, y, z, qx, qy, qz, qw]
            result = self.arm.rm_movej_p(pose, speed, 0, trajectory_connect, block)
            return result, "成功" if result == 0 else f"失败，错误码: {result}"
        except Exception as exc:
            return -1, f"异常: {exc}"

    def set_gripper_position(
        self, position: int, block: bool = True, timeout: int = 5
    ) -> Tuple[int, str]:
        """夹爪位置 1-1000"""
        if not self.is_connected:
            return -1, "未连接"

        pos = max(1, min(GRIPPER_POSITION_MAX, int(position)))

        if self.mode == "mock":
            logger.info("[Mock:%s] gripper -> %d", self.name, pos)
            time.sleep(0.2)
            return 0, "成功"

        try:
            result = self.arm.rm_set_gripper_position(pos, block, timeout)
            return result, "成功" if result == 0 else f"失败，错误码: {result}"
        except Exception as exc:
            return -1, f"异常: {exc}"
