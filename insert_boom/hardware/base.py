"""
硬件抽象层基类 — 步进电机、电缸、传感器统一接口

真实驱动实现时继承这些 ABC，Mock 实现用于无硬件联调。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional


class StepperMotorBase(ABC):
    """
    步进电机抽象接口

    映射关系（InsertBoom 项目）:
        stepper_1 / 图标1 : 绕线器
        stepper_2 / 图标5 : 压线机构
        stepper_3 / 图标2 : 刀片
        stepper_4 / 图标3 : 雷管插入
        stepper_5 / 图标4 : 引线收紧
    """

    def __init__(self, name: str, motor_id: int):
        self.name = name
        self.motor_id = motor_id
        # 脉冲当量：在 max_speed 流程速度下，每毫秒输出的脉冲数 (pulse/ms)
        self.pulses_per_ms: float = 10.0
        self.max_speed: int = 1000
        self.pulses_per_round: int = 10000

    def configure_motion(
        self,
        pulses_per_ms: float,
        max_speed: int = 1000,
        pulses_per_round: int = 10000,
    ) -> None:
        """从 system.yaml 加载运动标定参数"""
        self.pulses_per_ms = max(float(pulses_per_ms), 0.001)
        self.max_speed = max(int(max_speed), 1)
        self.pulses_per_round = max(int(pulses_per_round), 1)

    def effective_pulse_rate(self, speed: int) -> float:
        """
        将流程中的 speed 参数换算为实际脉冲率 (pulse/ms)。

        speed 与 max_speed 同量纲；在 max_speed 时输出 pulses_per_ms。
        """
        return self.pulses_per_ms * (max(int(speed), 0) / self.max_speed)

    def estimate_motion_seconds(self, pulse_distance: int, speed: int) -> float:
        """根据脉冲当量估算运动时间 (秒)"""
        rate_pps = self.effective_pulse_rate(speed) * 1000.0
        if rate_pps <= 0:
            return 0.0
        return abs(pulse_distance) / rate_pps

    def speed_to_rpm(self, speed: int) -> int:
        """雷赛驱动器：流程 speed → 转速 rpm"""
        rate_pps = self.effective_pulse_rate(speed) * 1000.0
        return max(1, int(rate_pps * 60.0 / self.pulses_per_round))

    def speed_to_device_units(self, speed: int) -> int:
        """RS485 文本协议等设备：流程 speed → 脉冲率 (pulse/s)"""
        return max(1, int(self.effective_pulse_rate(speed) * 1000.0))

    @abstractmethod
    def connect(self) -> bool:
        """建立通信连接"""

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""

    @abstractmethod
    def move_to_position(self, position: int, speed: int, timeout: float = 30.0) -> bool:
        """移动到绝对位置（脉冲/步数）"""

    @abstractmethod
    def move_relative(self, steps: int, speed: int, timeout: float = 30.0) -> bool:
        """相对运动"""

    @abstractmethod
    def move_to_home(self, speed: int, timeout: float = 30.0) -> bool:
        """回零"""

    @abstractmethod
    def stop(self) -> None:
        """立即停止"""

    @abstractmethod
    def is_moving(self) -> bool:
        """是否运动中"""

    @abstractmethod
    def get_position(self) -> int:
        """当前位置"""


class ElectricCylinderBase(ABC):
    """电缸抽象接口"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def connect(self) -> bool:
        """建立通信连接"""

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""

    @abstractmethod
    def extend(self, timeout: float = 5.0) -> bool:
        """伸出并等待到位"""

    @abstractmethod
    def retract(self, timeout: float = 5.0) -> bool:
        """缩回并等待到位"""

    @abstractmethod
    def stop(self) -> None:
        """急停"""

    @abstractmethod
    def is_extended(self) -> bool:
        """是否处于伸出状态"""

    @abstractmethod
    def is_retracted(self) -> bool:
        """是否处于缩回状态"""


class SensorBase(ABC):
    """
    传感器抽象接口

    read() 返回值语义由具体传感器定义，例如:
        winder_home: False=未遮挡=初始位, True=遮挡=不在初始位
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def connect(self) -> bool:
        """初始化传感器"""

    @abstractmethod
    def read(self) -> bool:
        """读取当前状态"""

    def wait_for(self, expected: bool, timeout: float = 5.0, poll_interval: float = 0.05) -> bool:
        """轮询等待达到期望状态"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.read() == expected:
                return True
            time.sleep(poll_interval)
        return False

    @abstractmethod
    def disconnect(self) -> None:
        """释放资源"""


class EmergencyStopBase(ABC):
    """急停按钮抽象"""

    @abstractmethod
    def is_pressed(self) -> bool:
        """急停是否被按下"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass
