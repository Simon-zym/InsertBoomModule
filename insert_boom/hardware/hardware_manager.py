"""
硬件管理器 — 统一管理所有底层设备

设备清单:
    步进电机 x5  → 各用 1 路 RS485 串口（绕线器/压线/刀片/插入/收紧）
    电缸     x2  → 各用 1 路 RS485 串口（夹雷管/切膜）
    传感器       → 绕线器初始位、压线到位等

模式:
    mock  — 不打开真实串口，用软件模拟（开发调试用）
    rs485 — 打开真实串口通信
"""

from __future__ import annotations

from typing import Dict, Optional

from insert_boom.hardware.base import (
    ElectricCylinderBase,
    EmergencyStopBase,
    SensorBase,
    StepperMotorBase,
)
from insert_boom.hardware.mock_devices import (
    MockElectricCylinder,
    MockEmergencyStop,
    MockSensor,
    MockStepperMotor,
)
from insert_boom.hardware.leadshine_devices import LeadShineStepperMotor
from insert_boom.hardware.rs485_devices import RS485ElectricCylinder, RS485StepperMotor
from insert_boom.log_helper import get_logger

logger = get_logger("hardware")

# 步进电机编号 → 中文名称（日志里显示用）
STEPPER_LABELS = {
    "stepper_1": "绕线器（图标1）",
    "stepper_2": "压线机构（图标5）",
    "stepper_3": "刀片（图标2）",
    "stepper_4": "雷管插入（图标3）",
    "stepper_5": "引线收紧（图标4）",
}


class HardwareManager:
    """硬件大门 — 所有步骤通过它操作电机/电缸/传感器"""

    def __init__(self, config: dict):
        self.config = config
        self.mode = config.get("hardware", {}).get("mode", "mock")
        self.steppers: Dict[str, StepperMotorBase] = {}
        self.cylinders: Dict[str, ElectricCylinderBase] = {}
        self.sensors: Dict[str, SensorBase] = {}
        self.emergency_stop: Optional[EmergencyStopBase] = None
        self._connected = False
        logger.info("硬件管理器初始化, 模式=%s", self.mode)

    def connect_all(self) -> bool:
        """一次性连接所有设备"""
        hw_cfg = self.config.get("hardware", {})

        if self.mode == "mock":
            self._build_mock_devices(hw_cfg)
        elif self.mode == "rs485":
            self._build_rs485_devices(hw_cfg)
        elif self.mode == "leadshine":
            self._build_leadshine_devices(hw_cfg)
        else:
            logger.error("不支持的硬件模式: %s（请用 mock、rs485 或 leadshine）", self.mode)
            return False

        # 逐个连接，任一失败则整体失败
        ok = True
        for name, motor in self.steppers.items():
            if motor.connect():
                logger.info("  ✓ 步进电机 %s (%s)", name, STEPPER_LABELS.get(name, ""))
            else:
                logger.error("  ✗ 步进电机 %s 连接失败", name)
                ok = False

        for name, cyl in self.cylinders.items():
            if cyl.connect():
                logger.info("  ✓ 电缸 %s", name)
            else:
                logger.error("  ✗ 电缸 %s 连接失败", name)
                ok = False

        for name, sensor in self.sensors.items():
            if sensor.connect():
                logger.info("  ✓ 传感器 %s", name)
            else:
                logger.error("  ✗ 传感器 %s 连接失败", name)
                ok = False

        if self.emergency_stop:
            ok = self.emergency_stop.connect() and ok

        self._connected = ok
        logger.info("硬件连接%s (共 %d 步进 + %d 电缸 + %d 传感器)",
                     "成功" if ok else "失败",
                     len(self.steppers), len(self.cylinders), len(self.sensors))
        return ok

    def disconnect_all(self) -> None:
        """安全断开所有设备"""
        logger.info("断开所有硬件连接...")
        for motor in self.steppers.values():
            motor.disconnect()
        for cyl in self.cylinders.values():
            cyl.disconnect()
        for sensor in self.sensors.values():
            sensor.disconnect()
        if self.emergency_stop:
            self.emergency_stop.disconnect()
        self._connected = False

    def emergency_stop(self) -> None:
        """急停 — 立即停止所有电机和电缸"""
        logger.warning("!!! 硬件急停 — 停止所有电机和电缸 !!!")
        for motor in self.steppers.values():
            motor.stop()
        for cyl in self.cylinders.values():
            cyl.stop()

    def check_emergency(self) -> bool:
        """检查急停按钮 — 返回 True 表示安全可以继续"""
        if self.emergency_stop is None:
            return True
        pressed = self.emergency_stop.is_pressed()
        if pressed:
            logger.warning("急停按钮已按下!")
        return not pressed

    def get_stepper(self, name: str) -> StepperMotorBase:
        if name not in self.steppers:
            raise KeyError(f"步进电机 '{name}' 不存在，可用: {list(self.steppers.keys())}")
        return self.steppers[name]

    def get_cylinder(self, name: str) -> ElectricCylinderBase:
        if name not in self.cylinders:
            raise KeyError(f"电缸 '{name}' 不存在，可用: {list(self.cylinders.keys())}")
        return self.cylinders[name]

    def get_sensor(self, name: str) -> SensorBase:
        if name not in self.sensors:
            raise KeyError(f"传感器 '{name}' 不存在，可用: {list(self.sensors.keys())}")
        return self.sensors[name]

    def _serial_params(self, hw_cfg: dict, device_cfg: dict) -> dict:
        defaults = hw_cfg.get("serial_defaults", {})
        return {
            "baudrate": int(device_cfg.get("baudrate", defaults.get("baudrate", 115200))),
            "timeout": float(device_cfg.get("timeout", defaults.get("timeout", 0.5))),
            "motion_timeout": float(
                device_cfg.get("motion_timeout", defaults.get("motion_timeout", 30.0))
            ),
        }

    def _stepper_motion_config(self, hw_cfg: dict, cfg: dict) -> dict:
        """步进脉冲当量等运动标定（每电机可独立配置）"""
        ls = hw_cfg.get("leadshine_defaults", {})
        return {
            "pulses_per_ms": float(cfg.get("pulses_per_ms", 10.0)),
            "max_speed": int(cfg.get("max_speed", 1000)),
            "pulses_per_round": int(
                cfg.get("leadshine", {}).get("pulses_per_round", ls.get("pulses_per_round", 10000))
            ),
        }

    def _apply_stepper_motion(self, motor: StepperMotorBase, hw_cfg: dict, cfg: dict) -> None:
        motion = self._stepper_motion_config(hw_cfg, cfg)
        motor.configure_motion(**motion)

    def _build_mock_devices(self, hw_cfg: dict) -> None:
        """Mock 模式: 创建模拟设备，日志里标注对应串口"""
        logger.info("创建 Mock 硬件设备...")
        for key, cfg in hw_cfg.get("steppers", {}).items():
            port = cfg.get("port", "N/A")
            motor = MockStepperMotor(key, int(cfg.get("id", 0)), int(cfg.get("home_position", 0)))
            motor.port = port  # type: ignore[attr-defined]
            self._apply_stepper_motion(motor, hw_cfg, cfg)
            self.steppers[key] = motor
            logger.debug("  Mock %s [%s] → 串口 %s", STEPPER_LABELS.get(key, key), key, port)

        for key, cfg in hw_cfg.get("cylinders", {}).items():
            cyl = MockElectricCylinder(key)
            cyl.port = cfg.get("port", "N/A")  # type: ignore[attr-defined]
            self.cylinders[key] = cyl
            logger.debug("  Mock %s → 串口 %s", key, cfg.get("port"))

        for key, cfg in hw_cfg.get("sensors", {}).items():
            self.sensors[key] = MockSensor(key, bool(cfg.get("initial_value", False)))

        self.emergency_stop = MockEmergencyStop()

    def _build_leadshine_devices(self, hw_cfg: dict) -> None:
        """
        雷赛 Modbus 步进 + RS485 文本协议电缸。

        步进: hd_ware_tool → LeadShineStepperMotor
        电缸: 仍用 RS485ElectricCylinder（EXTEND/RETRACT 文本命令）
        配置合并顺序: leadshine_defaults ← steppers.*.leadshine ← slave_id
        """
        logger.info("创建雷赛步进 + RS485 电缸设备...")
        defaults = dict(hw_cfg.get("leadshine_defaults", {}))
        serial_defaults = hw_cfg.get("serial_defaults", {})
        defaults.setdefault("delay_read_write", serial_defaults.get("delay_read_write", 0.05))

        for key, cfg in hw_cfg.get("steppers", {}).items():
            params = self._serial_params(hw_cfg, cfg)
            port = cfg.get("port")
            if not port:
                raise ValueError(f"{key} 未配置串口 port，请检查 system.yaml")

            motor_ls = dict(defaults)
            motor_ls.update(cfg.get("leadshine", {}))
            motor_ls.setdefault("slave_id", cfg.get("slave_id", cfg.get("id", 1)))

            self.steppers[key] = LeadShineStepperMotor(
                name=key,
                motor_id=int(cfg.get("id", 0)),
                port=port,
                baudrate=params["baudrate"],
                home_position=int(cfg.get("home_position", 0)),
                motion_timeout=params["motion_timeout"],
                delay_read_write=float(motor_ls.get("delay_read_write", 0.05)),
                leadshine_cfg=motor_ls,
            )
            self._apply_stepper_motion(self.steppers[key], hw_cfg, cfg)
            logger.info(
                "  LeadShine %s → %s @ %d slave=%s",
                STEPPER_LABELS.get(key, key),
                port,
                params["baudrate"],
                motor_ls.get("slave_id"),
            )

        for key, cfg in hw_cfg.get("cylinders", {}).items():
            params = self._serial_params(hw_cfg, cfg)
            port = cfg.get("port")
            if not port:
                raise ValueError(f"{key} 未配置串口 port")
            self.cylinders[key] = RS485ElectricCylinder(
                name=key,
                port=port,
                baudrate=params["baudrate"],
                timeout=params["timeout"],
                motion_timeout=params["motion_timeout"],
            )
            logger.info("  RS485 %s → %s", key, port)

        for key, cfg in hw_cfg.get("sensors", {}).items():
            self.sensors[key] = MockSensor(key, bool(cfg.get("initial_value", False)))

        self.emergency_stop = MockEmergencyStop()

    def _build_rs485_devices(self, hw_cfg: dict) -> None:
        """RS485 模式: 创建真实串口设备"""
        logger.info("创建 RS485 硬件设备...")
        for key, cfg in hw_cfg.get("steppers", {}).items():
            params = self._serial_params(hw_cfg, cfg)
            port = cfg.get("port")
            if not port:
                raise ValueError(f"{key} 未配置串口 port，请检查 system.yaml")
            self.steppers[key] = RS485StepperMotor(
                name=key,
                motor_id=int(cfg.get("id", 0)),
                port=port,
                baudrate=params["baudrate"],
                home_position=int(cfg.get("home_position", 0)),
                timeout=params["timeout"],
                motion_timeout=params["motion_timeout"],
            )
            self._apply_stepper_motion(self.steppers[key], hw_cfg, cfg)
            logger.info("  RS485 %s → %s @ %d",
                          STEPPER_LABELS.get(key, key), port, params["baudrate"])

        for key, cfg in hw_cfg.get("cylinders", {}).items():
            params = self._serial_params(hw_cfg, cfg)
            port = cfg.get("port")
            if not port:
                raise ValueError(f"{key} 未配置串口 port")
            self.cylinders[key] = RS485ElectricCylinder(
                name=key, port=port,
                baudrate=params["baudrate"],
                timeout=params["timeout"],
                motion_timeout=params["motion_timeout"],
            )
            logger.info("  RS485 %s → %s", key, port)

        for key, cfg in hw_cfg.get("sensors", {}).items():
            self.sensors[key] = MockSensor(key, bool(cfg.get("initial_value", False)))

        self.emergency_stop = MockEmergencyStop()

    def simulate_winder_reached_home(self) -> None:
        """Mock 专用: 模拟绕线器到达初始位（传感器变为未遮挡）"""
        sensor = self.sensors.get("winder_home")
        if isinstance(sensor, MockSensor):
            sensor.set_value(False)
            logger.info("[Mock] 绕线器传感器 → 未遮挡（已到初始位）")
