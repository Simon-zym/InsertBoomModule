"""
雷赛电机初始化与工程单位换算示例
================================

LeadShineMotorProfile 演示完整上电初始化流程：
    脉冲比 → 闭环模式 → DI/DO 映射 → 编码器 → PR/回零参数 → 回零 → 设零 → 保存

pulse_to_distance_ratio 用于将 pulse 换算为米，按丝杆/减速比现场标定。
默认 50000/0.375 仅为示例，请在 system.yaml 或配置编辑器中按实际机构修改。
"""

from __future__ import annotations

from hd_ware_tool.leadshine_motor_ctl import LeadShineMotorControl
from hd_ware_tool.modbus_motor_ctl import ModbusRtuMaster


class LeadShineMotorProfile(LeadShineMotorControl):
    """带初始化流程与米/脉冲换算的雷赛电机封装（单机调试参考实现）"""

    def __init__(
        self,
        master: ModbusRtuMaster,
        slave_id: int,
        mode: str = "CLOSE_LOOP",
        acceleration: int = 50,
        deceleration: int = 50,
        pulse_to_distance_ratio: float = 50000 / 0.375,
    ):
        """
        :param pulse_to_distance_ratio: 每米对应的脉冲数，pulse = 米 × ratio
        """
        super().__init__(master, slave_id, mode, acceleration, deceleration)
        self.pulse_to_distance_ratio = pulse_to_distance_ratio

    def init_motor(self, auto_home: bool = True) -> bool:
        """
        按项目默认参数初始化电机。

        顺序与配置编辑器「雷赛步进 (全局)」中的默认值一致，
        可在 system.yaml 的 leadshine_defaults 中覆盖。
        """
        self.set_pulses_per_round(10000)
        self.set_motor_mode(self.mode)
        self.set_input_type(0x0147, 0x26)  # DI2 → 反向限位
        self.set_input_type(0x0149, 0x25)  # DI3 → 正向限位
        self.set_output_type(0x0157, 0x05)   # DO1 通用输出
        self.set_output_type(0x0159, 0x05)   # DO2 通用输出
        self.set_output_type(0x015B, 0x05)   # DO3 通用输出
        self.set_encoder_resolution(4000)    # 1000 线 × 4 倍频
        self.set_pr_parameter(0, 0, 0, 0)
        self.set_home_parameter(0, 0, 0, 0, 0, 0)  # 反向限位回零

        if auto_home:
            self.return_home()
            if not self.wait_to_zero_motor_stop():
                return False
            self.set_current_position_as_zero()

        self.save_parameters()
        return True

    def get_current_position_m(self) -> float:
        """当前位置，单位米"""
        return self.get_motor_position() / self.pulse_to_distance_ratio

    def move_to_position_m(self, position_m: float, velocity: int = 300) -> None:
        """绝对运动到指定位置（米）"""
        pulses = int(position_m * self.pulse_to_distance_ratio + 0.5)
        self.set_motor_absolute_position_mode(pulses, velocity=velocity)

    def move_relative_m(self, distance_m: float, velocity: int = 300) -> None:
        """相对运动（米）"""
        pulses = int(distance_m * self.pulse_to_distance_ratio + 0.5)
        self.set_motor_relative_position_mode(pulses, velocity=velocity)
