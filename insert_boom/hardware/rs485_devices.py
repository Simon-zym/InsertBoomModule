"""
RS485 真实设备驱动 — 步进电机 / 电缸

协议说明（可按现场控制器修改命令格式）:
    步进: MOVE_ABS:<pos>,<speed> | MOVE_REL:<steps>,<speed> | HOME:<speed> | STOP | POS?
    电缸: EXTEND | RETRACT | STOP | STATUS?
    应答: OK / ERR:<code> / POS:<n> / STATUS:EXTENDED|RETRACTED|MOVING
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from insert_boom.hardware.base import ElectricCylinderBase, StepperMotorBase
from insert_boom.hardware.serial_transport import SerialTransport

logger = logging.getLogger("insert_boom.hardware.rs485")


class RS485StepperMotor(StepperMotorBase):
    """单路 RS485 步进电机"""

    def __init__(
        self,
        name: str,
        motor_id: int,
        port: str,
        baudrate: int = 115200,
        home_position: int = 0,
        timeout: float = 0.5,
        motion_timeout: float = 30.0,
    ):
        super().__init__(name, motor_id)
        self.home_position = home_position
        self.motion_timeout = motion_timeout
        self._position = home_position
        self._moving = False
        self._transport = SerialTransport(port, baudrate, timeout, device_name=name)

    def connect(self) -> bool:
        return self._transport.connect()

    def disconnect(self) -> None:
        self._transport.disconnect()

    def _send(self, cmd: str) -> bool:
        logger.debug("[%s] >> %s", self.name, cmd)
        resp = self._transport.write_read_line(cmd, timeout=self.motion_timeout)
        if resp is None:
            logger.error("[%s] 无应答: %s", self.name, cmd)
            return False
        logger.debug("[%s] << %s", self.name, resp)
        if resp.startswith("ERR"):
            logger.error("[%s] 命令失败: %s", self.name, resp)
            return False
        return resp.startswith("OK") or resp.startswith("POS:")

    def _query_position(self) -> Optional[int]:
        resp = self._transport.write_read_line("POS?", timeout=2.0)
        if resp and resp.startswith("POS:"):
            try:
                return int(resp.split(":", 1)[1])
            except ValueError:
                return None
        return None

    def move_to_position(self, position: int, speed: int, timeout: float = 30.0) -> bool:
        self._moving = True
        device_speed = self.speed_to_device_units(speed)
        ok = self._send(f"MOVE_ABS:{position},{device_speed}")
        if ok:
            self._position = position
        self._moving = False
        return ok

    def move_relative(self, steps: int, speed: int, timeout: float = 30.0) -> bool:
        self._moving = True
        device_speed = self.speed_to_device_units(speed)
        ok = self._send(f"MOVE_REL:{steps},{device_speed}")
        if ok:
            self._position += steps
        self._moving = False
        return ok

    def move_to_home(self, speed: int, timeout: float = 30.0) -> bool:
        self._moving = True
        device_speed = self.speed_to_device_units(speed)
        ok = self._send(f"HOME:{device_speed}")
        if ok:
            self._position = self.home_position
        self._moving = False
        return ok

    def stop(self) -> None:
        self._transport.write_line("STOP")
        self._moving = False

    def is_moving(self) -> bool:
        return self._moving

    def get_position(self) -> int:
        pos = self._query_position()
        if pos is not None:
            self._position = pos
        return self._position


class RS485ElectricCylinder(ElectricCylinderBase):
    """单路 RS485 电缸"""

    def __init__(
        self,
        name: str,
        port: str,
        baudrate: int = 115200,
        timeout: float = 0.5,
        motion_timeout: float = 10.0,
    ):
        super().__init__(name)
        self.motion_timeout = motion_timeout
        self._extended = False
        self._transport = SerialTransport(port, baudrate, timeout, device_name=name)

    def connect(self) -> bool:
        ok = self._transport.connect()
        if ok:
            self._extended = False
        return ok

    def disconnect(self) -> None:
        self._transport.disconnect()

    def _send(self, cmd: str) -> bool:
        logger.debug("[%s] >> %s", self.name, cmd)
        resp = self._transport.write_read_line(cmd, timeout=self.motion_timeout)
        if resp is None:
            return False
        logger.debug("[%s] << %s", self.name, resp)
        return resp.startswith("OK") or resp.startswith("STATUS:")

    def _refresh_status(self) -> None:
        resp = self._transport.write_read_line("STATUS?", timeout=2.0)
        if resp and resp.startswith("STATUS:"):
            state = resp.split(":", 1)[1].strip().upper()
            self._extended = state == "EXTENDED"

    def extend(self, timeout: float = 5.0) -> bool:
        # 先等命令应答，再开始轮询 STATUS（deadline 必须在 _send 之后）
        if not self._send("EXTEND"):
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._refresh_status()
            if self._extended:
                return True
            time.sleep(0.05)
        return False

    def retract(self, timeout: float = 5.0) -> bool:
        if not self._send("RETRACT"):
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._refresh_status()
            if not self._extended:
                return True
            time.sleep(0.05)
        return False

    def stop(self) -> None:
        self._transport.write_line("STOP")

    def is_extended(self) -> bool:
        self._refresh_status()
        return self._extended

    def is_retracted(self) -> bool:
        self._refresh_status()
        return not self._extended
