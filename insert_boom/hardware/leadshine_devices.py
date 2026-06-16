"""
雷赛步进电机驱动 — 实现 StepperMotorBase
==========================================

桥接层：将 InsertBoom 统一的步进接口（脉冲/步、rpm）映射到 hd_ware_tool 雷赛 API。

配置来源 (config/system.yaml)
-----------------------------
hardware.leadshine_defaults   全局默认
hardware.steppers.<name>.leadshine   单电机覆盖
hardware.steppers.<name>.slave_id    Modbus 从站地址
hardware.steppers.<name>.pulses_per_ms  脉冲当量 (pulse/ms，在 max_speed 下)
hardware.steppers.<name>.max_speed      流程速度上限，与 workflow 中 speed 对应

装配流程中的 stepper_1~5 通过 HardwareManager.get_stepper() 调用，
无需步骤代码感知 Modbus 细节。
"""

from __future__ import annotations

import logging
from typing import Any

from insert_boom.hardware.base import StepperMotorBase
from hd_ware_tool.leadshine_motor_ctl import LeadShineMotorControl
from hd_ware_tool.modbus_motor_ctl import ModbusRtuMaster

logger = logging.getLogger("insert_boom.hardware.leadshine")

# get_motor_status() 返回值 → 界面/日志中文
MOTOR_STATUS_ZH = {
    1: "运行中",
    2: "回零完成",
    3: "路径完成",
    4: "空闲/其他",
}


class LeadShineStepperMotor(StepperMotorBase):
    """
    单路雷赛步进电机。

    连接时按配置写入 DI/DO、PR、回零等参数；可选 enable_on_connect / auto_home_on_init。
    运动接口阻塞等待路径完成或超时。
    """

    def __init__(
        self,
        name: str,
        motor_id: int,
        port: str,
        baudrate: int = 115200,
        home_position: int = 0,
        motion_timeout: float = 30.0,
        delay_read_write: float = 0.05,
        leadshine_cfg: dict[str, Any] | None = None,
        defaults: dict[str, Any] | None = None,
    ):
        """
        :param name: 逻辑名，如 stepper_1
        :param motor_id: 配置 id，用于日志
        :param port: 串口路径，每路电机独立
        :param leadshine_cfg: 已合并 defaults 后的雷赛参数字典
        """
        super().__init__(name, motor_id)
        self.home_position = home_position
        self.motion_timeout = motion_timeout
        self.baudrate = baudrate
        self.delay_read_write = delay_read_write
        self.port = port
        self.leadshine_cfg = leadshine_cfg or {}
        self._position = home_position
        self._moving = False

        merged = dict(defaults or {})
        merged.update(self.leadshine_cfg)
        self.cfg = merged
        self.slave_id = int(merged.get("slave_id", motor_id))
        self.mode = str(merged.get("mode", "CLOSE_LOOP"))
        self.acceleration = int(merged.get("acceleration", 50))
        self.deceleration = int(merged.get("deceleration", 50))
        self.default_velocity = int(merged.get("velocity", 300))
        self.pulses_per_round = int(merged.get("pulses_per_round", 10000))
        self.encoder_resolution = int(merged.get("encoder_resolution", 4000))
        self.peak_current = int(merged.get("peak_current", 10))
        self.auto_home_on_init = bool(merged.get("auto_home_on_init", True))
        self.enable_on_connect = bool(merged.get("enable_on_connect", False))

        self._master: ModbusRtuMaster | None = None
        self._motor: LeadShineMotorControl | None = None

    def connect(self) -> bool:
        """打开串口、下发基础参数，可选使能与上电回零"""
        try:
            self._master = ModbusRtuMaster(
                self.port,
                baudrate=self.baudrate,
                delay_read_write=self.delay_read_write,
            )
            self._motor = LeadShineMotorControl(
                self._master,
                self.slave_id,
                mode=self.mode,
                acceleration=self.acceleration,
                deceleration=self.deceleration,
            )
            self._apply_base_parameters()
            if self.enable_on_connect:
                self._motor.enable_motor(True)
            if self.auto_home_on_init:
                self._motor.return_home()
                if not self._motor.wait_to_zero_motor_stop(timeout=self.motion_timeout):
                    logger.error("[%s] 上电回零超时", self.name)
                    return False
                self._motor.set_current_position_as_zero()
                self._position = self.home_position
            logger.info("[%s] 雷赛电机已连接 port=%s slave=%d", self.name, self.port, self.slave_id)
            return True
        except Exception as exc:
            logger.error("[%s] 雷赛电机连接失败: %s", self.name, exc)
            return False

    def _apply_base_parameters(self) -> None:
        """将 system.yaml 中的雷赛参数写入驱动器（连接后执行一次）"""
        assert self._motor is not None
        m = self._motor
        m.set_pulses_per_round(self.pulses_per_round)
        m.set_motor_mode(self.mode)
        m.set_peak_current(self.peak_current)
        if self.mode == "CLOSE_LOOP":
            m.set_encoder_resolution(self.encoder_resolution)

        di_neg = self.cfg.get("di_neg_limit")
        di_neg_type = self.cfg.get("di_neg_limit_type")
        di_pos = self.cfg.get("di_pos_limit")
        di_pos_type = self.cfg.get("di_pos_limit_type")
        if di_neg is not None and di_neg_type is not None:
            m.set_input_type(int(di_neg), int(di_neg_type))
        if di_pos is not None and di_pos_type is not None:
            m.set_input_type(int(di_pos), int(di_pos_type))

        for addr_key, type_key in (
            ("do1", "do1_type"),
            ("do2", "do2_type"),
            ("do3", "do3_type"),
        ):
            addr = self.cfg.get(addr_key)
            typ = self.cfg.get(type_key)
            if addr is not None and typ is not None:
                m.set_output_type(int(addr), int(typ))

        pr = self.cfg.get("pr_parameter", {})
        m.set_pr_parameter(
            int(pr.get("ctrg", 0)),
            int(pr.get("software_limit", 0)),
            int(pr.get("power_on_home", 0)),
            int(pr.get("level_trigger", 0)),
        )
        home = self.cfg.get("home_parameter", {})
        m.set_home_parameter(
            int(home.get("direction", 0)),
            int(home.get("move_to_position", 0)),
            int(home.get("home_mode", 0)),
            int(home.get("single_z", 0)),
            int(home.get("current_as_home", 0)),
            int(home.get("with_z_signal", 0)),
        )

    def disconnect(self) -> None:
        """停止运动并释放引用（串口由 ModbusRtuMaster 单例保持，进程内可复用）"""
        if self._motor:
            try:
                self._motor.stop_motor()
            except Exception:
                pass
        self._motor = None
        self._master = None

    def _wait_done(self, timeout: float) -> bool:
        """阻塞等待 PR 路径完成"""
        assert self._motor is not None
        ok = self._motor.wait_until_motor_stop(timeout=timeout)
        self._moving = False
        if ok:
            self._position = self._motor.get_motor_position()
        return ok

    def move_to_position(self, position: int, speed: int, timeout: float = 30.0) -> bool:
        """绝对位置运动，position 单位 pulse；speed 经脉冲当量换算为 rpm"""
        if not self._motor:
            return False
        self._moving = True
        rpm = self.speed_to_rpm(speed) if speed else self.default_velocity
        self._motor.set_motor_absolute_position_mode(position, velocity=rpm)
        return self._wait_done(timeout)

    def move_relative(self, steps: int, speed: int, timeout: float = 30.0) -> bool:
        """相对运动，steps 单位 pulse"""
        if not self._motor:
            return False
        self._moving = True
        rpm = self.speed_to_rpm(speed) if speed else self.default_velocity
        self._motor.set_motor_relative_position_mode(steps, velocity=rpm)
        return self._wait_done(timeout)

    def move_to_home(self, speed: int, timeout: float = 30.0) -> bool:
        """限位/原点回零（speed 参数保留兼容，实际速度由驱动器内参数决定）"""
        if not self._motor:
            return False
        self._moving = True
        self._motor.return_home()
        ok = self._motor.wait_to_zero_motor_stop(timeout=timeout)
        self._moving = False
        if ok:
            self._position = self.home_position
        return ok

    def stop(self) -> None:
        """急停 — 写 0x6002 停止命令"""
        if self._motor:
            self._motor.stop_motor()
        self._moving = False

    def is_moving(self) -> bool:
        if not self._motor:
            return self._moving
        status = self._motor.get_motor_status()
        return status == 1 or self._moving

    def get_position(self) -> int:
        """当前位置 pulse，失败时返回缓存值"""
        if self._motor:
            try:
                self._position = self._motor.get_motor_position()
            except Exception:
                pass
        return self._position

    def get_velocity(self) -> int:
        """当前速度 rpm（开环模式恒为 0）"""
        if not self._motor:
            return 0
        try:
            return self._motor.get_motor_velocity()
        except Exception:
            return 0

    def get_status_text(self) -> str:
        """供配置编辑器调试面板显示"""
        if not self._motor:
            return "未连接"
        status = self._motor.get_motor_status()
        return MOTOR_STATUS_ZH.get(status, f"未知({status})")

    def get_raw_motor(self) -> LeadShineMotorControl | None:
        """暴露底层 LeadShineMotorControl，供配置编辑器调试按钮调用"""
        return self._motor
