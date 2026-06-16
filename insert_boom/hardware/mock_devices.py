"""
Mock 硬件实现 — 无真实设备时可跑通全流程

用于开发联调；上线时替换为 serial/gpio/modbus 真实驱动。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional

from insert_boom.hardware.base import (
    ElectricCylinderBase,
    EmergencyStopBase,
    SensorBase,
    StepperMotorBase,
)

logger = logging.getLogger("insert_boom.hardware.mock")


class MockStepperMotor(StepperMotorBase):
    """Mock 步进电机 — 模拟运动延迟"""

    def __init__(self, name: str, motor_id: int, home_position: int = 0):
        super().__init__(name, motor_id)
        self._position = home_position
        self._home_position = home_position
        self._moving = False
        self._connected = False
        self._lock = threading.Lock()

    def connect(self) -> bool:
        self._connected = True
        logger.info("[MockStepper:%s] 已连接, 当前位置=%d", self.name, self._position)
        return True

    def disconnect(self) -> None:
        self._connected = False

    def _simulate_move(self, target: int, speed: int) -> bool:
        with self._lock:
            self._moving = True
        distance = abs(target - self._position)
        delay = min(0.05 + distance / max(speed, 1) * 0.001, 2.0)
        time.sleep(delay)
        with self._lock:
            self._position = target
            self._moving = False
        logger.info("[MockStepper:%s] 到达位置 %d", self.name, target)
        return True

    def move_to_position(self, position: int, speed: int, timeout: float = 30.0) -> bool:
        if not self._connected:
            return False
        logger.info("[MockStepper:%s] move_to_position(%d, speed=%d)", self.name, position, speed)
        return self._simulate_move(position, speed)

    def move_relative(self, steps: int, speed: int, timeout: float = 30.0) -> bool:
        return self.move_to_position(self._position + steps, speed, timeout)

    def move_to_home(self, speed: int, timeout: float = 30.0) -> bool:
        return self.move_to_position(self._home_position, speed, timeout)

    def stop(self) -> None:
        with self._lock:
            self._moving = False
        logger.warning("[MockStepper:%s] 急停", self.name)

    def is_moving(self) -> bool:
        return self._moving

    def get_position(self) -> int:
        return self._position

    def set_position(self, position: int) -> None:
        """Mock 专用：手动设置位置（测试用）"""
        self._position = position


class MockElectricCylinder(ElectricCylinderBase):
    """Mock 电缸"""

    def __init__(self, name: str):
        super().__init__(name)
        self._extended = False
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        self._extended = False
        logger.info("[MockCylinder:%s] 已连接（初始缩回）", self.name)
        return True

    def disconnect(self) -> None:
        self._connected = False

    def extend(self, timeout: float = 5.0) -> bool:
        if not self._connected:
            return False
        logger.info("[MockCylinder:%s] 伸出", self.name)
        time.sleep(0.3)
        self._extended = True
        return True

    def retract(self, timeout: float = 5.0) -> bool:
        if not self._connected:
            return False
        logger.info("[MockCylinder:%s] 缩回", self.name)
        time.sleep(0.3)
        self._extended = False
        return True

    def stop(self) -> None:
        logger.warning("[MockCylinder:%s] 急停", self.name)

    def is_extended(self) -> bool:
        return self._extended

    def is_retracted(self) -> bool:
        return not self._extended


class MockSensor(SensorBase):
    """
    Mock 传感器

    initial_value: 初始读数
        winder_home 传感器: False=未遮挡=在初始位
    """

    def __init__(self, name: str, initial_value: bool = False):
        super().__init__(name)
        self._value = initial_value
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        logger.info("[MockSensor:%s] 已连接, 初始值=%s", self.name, self._value)
        return True

    def disconnect(self) -> None:
        self._connected = False

    def read(self) -> bool:
        return self._value

    def set_value(self, value: bool) -> None:
        """Mock 专用：模拟传感器状态变化"""
        self._value = value
        logger.info("[MockSensor:%s] 设为 %s", self.name, value)


class MockEmergencyStop(EmergencyStopBase):
    """Mock 急停 — 默认未按下"""

    def __init__(self):
        self._pressed = False
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_pressed(self) -> bool:
        return self._pressed

    def set_pressed(self, pressed: bool) -> None:
        self._pressed = pressed
