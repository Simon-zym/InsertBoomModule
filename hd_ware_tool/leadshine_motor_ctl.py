"""
雷赛步进电机 Modbus 控制 — 基于 PR 模式寄存器
==============================================

常用寄存器（协议地址）
----------------------
0x0001  每转脉冲数          0x0003  开环/闭环模式
0x000F  软件使能            0x0191  峰值电流 (0.1A)
0x0233  编码器分辨率        0x1003  运行状态字
0x1046  当前速度 (2字)      0x1801  保存/清除报警
0x6000  PR 参数             0x6002  触发命令 (回零/设零/急停)
0x600A  回零参数            0x602C  当前位置 (2字, pulse)
0x6200  PR 路径块 (8字)     0x2110  IO 输出

PR 路径块 0x6200 格式 (8 寄存器)
---------------------------------
[0] 模式: 0x0001绝对 / 0x0041相对 / 0x0002速度
[1][2] 位置高/低 16 位
[3] 速度 rpm
[4][5] 加减速
[6] 保留
[7] 触发字 0x0010

状态字 0x1003 bit4~6
--------------------
0x0 运行中 | 0x4/0x5 回零完成 | 0x7 路径完成
"""

from __future__ import annotations

import time

from hd_ware_tool.modbus_motor_ctl import MotorControl, ModbusRtuMaster


def _registers_to_int32(high: int, low: int) -> int:
    """两个 16 位寄存器合并为有符号 32 位整数"""
    val = ((high & 0xFFFF) << 16) | (low & 0xFFFF)
    if val >= 0x80000000:
        val -= 0x100000000
    return val


class LeadShineMotorControl(MotorControl):
    """
    雷赛 DM 系列步进驱动器控制类。

    光电限位接线：黑线 → DI，棕 +24V / 蓝 GND，COM → 24V。
    配置 DI 功能见 set_input_type()，限位示例见 test_leadshine_motor_ctl.py。
    """

    def __init__(
        self,
        master: ModbusRtuMaster,
        slave_id: int,
        mode: str = "CLOSE_LOOP",
        acceleration: int = 50,
        deceleration: int = 50,
    ):
        """
        雷赛步进电机控制类，光电开关：黑线接 IO，棕正蓝负，COM 接 24V
        :param master: Modbus RTU 主机
        :param slave_id: 从机地址
        :param mode: CLOSE_LOOP 闭环 / OPEN_LOOP 开环
        :param acceleration: 加速度 ms/1000rpm
        :param deceleration: 减速度 ms/1000rpm
        """
        super().__init__(master, slave_id)
        self.mode = mode
        self.acceleration = acceleration
        self.deceleration = deceleration

    def enable_motor(self, enable: bool = True) -> None:
        """软件强制使能"""
        self.write_single_holding(0x000F, 1 if enable else 0)

    def set_pulses_per_round(self, pulses: int = 10000) -> None:
        """设置电机每转脉冲数"""
        self.write_single_holding(0x0001, pulses)

    def set_motor_mode(self, mode: str = "CLOSE_LOOP") -> None:
        """设置电机模式"""
        if mode == "CLOSE_LOOP":
            self.write_single_holding(0x0003, 0x02)
        else:
            self.write_single_holding(0x0003, 0x00)
        self.mode = mode

    def set_input_type(self, address: int, input_type: int) -> None:
        """配置 DI 输入类型，地址 0x0145~0x0151"""
        if address < 0x0145 or address > 0x0151:
            self.log.error_show(f"输入地址错误: {address:#x}, 范围 0x0145~0x0151")
            return
        if input_type < 0x19 or input_type > 0x2C:
            self.log.error_show(f"输入类型错误: {input_type:#x}, 范围 0x19~0x2C")
            return
        self.write_single_holding(address, input_type)

    def set_output_type(self, address: int, output_type: int) -> None:
        """配置 DO 输出类型，地址 0x0157~0x015B"""
        if address < 0x0157 or address > 0x015B:
            self.log.error_show(f"输出地址错误: {address:#x}, 范围 0x0157~0x015B")
            return
        if output_type < 0x05 or output_type > 0x25:
            self.log.error_show(f"输出类型错误: {output_type:#x}, 范围 0x05~0x25")
            return
        self.write_single_holding(address, output_type)

    def set_encoder_resolution(self, resolution: int = 4000) -> None:
        """设置编码器分辨率（仅闭环模式）"""
        if self.mode != "CLOSE_LOOP":
            self.log.error_show(f"电机模式为 {self.mode}，不能设置编码器分辨率")
            return
        self.write_single_holding(0x0233, resolution)

    def set_pr_parameter(
        self,
        ctrg: int = 0,
        software_limit: int = 0,
        power_on_home: int = 0,
        level_trigger: int = 0,
    ) -> None:
        """设置 PR 参数"""
        value = ctrg | (software_limit << 1) | (power_on_home << 2) | (level_trigger << 4)
        self.write_single_holding(0x6000, value)

    def set_home_parameter(
        self,
        direction: int = 0,
        move_to_position: int = 0,
        home_mode: int = 0,
        single_z: int = 0,
        current_as_home: int = 0,
        with_z_signal: int = 0,
    ) -> None:
        """设置回零参数"""
        value = (
            direction
            | (move_to_position << 1)
            | (home_mode << 2)
            | (single_z << 3)
            | (current_as_home << 5)
            | (with_z_signal << 8)
        )
        self.write_single_holding(0x600A, value)

    def set_current_position_as_zero(self) -> None:
        """当前位置设为零点"""
        self.write_single_holding(0x6002, 0x21)

    def set_peak_current(self, current: int = 10) -> None:
        """峰值电流，单位 0.1A"""
        self.write_single_holding(0x0191, current)

    def save_parameters(self) -> None:
        """保存参数到驱动器"""
        self.write_single_holding(0x1801, 0x2211)

    def get_motor_status(self) -> int | None:
        """
        读取运行状态
        1=运行中 2=回零完成 3=路径完成 4=其他/空闲
        """
        try:
            data = self.read_holdings(0x1003, 1)
            status_bits = (data[0] >> 4) & 0x07
            if status_bits == 0x00:
                return 1
            if status_bits in (0x04, 0x05):
                return 2
            if status_bits == 0x07:
                return 3
            return 4
        except Exception as e:
            self.log.error_show(f"获取电机状态失败: {e}")
            return None

    def get_motor_move_result(self) -> bool:
        """True=运动完成，False=仍在运动或失败"""
        try:
            status = self.get_motor_status()
            if status in (2, 3):
                self.log.finish_show(f"电机移动成功: {status}")
                return True
            self.log.warn_show(f"电机正在移动或移动失败: {status}")
            return False
        except Exception as e:
            self.log.error_show(f"获取电机移动结果失败: {e}")
            return False

    def return_home(self) -> None:
        """触发回零"""
        self.write_single_holding(0x6002, 0x20)

    def stop_motor(self) -> None:
        """立即停止"""
        self.write_single_holding(0x6002, 0x40)

    def reset_current_warning(self) -> None:
        """清除当前报警"""
        self.write_single_holding(0x1801, 0x1111)

    def set_io_out(self, index: int, output: bool = True) -> None:
        """IO 输出，低电平有效；index 为 1~3"""
        value = 1 if output else 0
        self.write_single_holding(0x2110 + index - 1, value)

    def wait_until_motor_stop(self, timeout: float = 60.0, poll: float = 0.05) -> bool:
        """等待路径运动完成"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_motor_status()
            if status == 3:
                return True
            if status is None:
                return False
            time.sleep(poll)
        self.log.warn_show(f"等待运动完成超时 ({timeout}s)")
        return False

    def wait_to_zero_motor_stop(self, timeout: float = 120.0, poll: float = 0.05) -> bool:
        """等待回零完成"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_motor_status()
            if status in (2, 3):
                return True
            if status is None:
                return False
            time.sleep(poll)
        self.log.warn_show(f"等待回零完成超时 ({timeout}s)")
        return False

    def set_motor_velocity_mode(self, velocity: int) -> None:
        """速度模式，velocity 单位 rpm"""
        self.write_multiple_holdings(
            0x6200,
            8,
            [0x0002, 0x0000, 0x0000, velocity, self.acceleration, self.deceleration, 0x0000, 0x0010],
        )

    def set_motor_absolute_position_mode(self, position: int, velocity: int = 300) -> None:
        """
        绝对位置模式 — 写入 PR 路径块并触发运动。

        :param position: 目标位置 (pulse)
        :param velocity: 速度 (rpm)
        """
        pos_high = (position >> 16) & 0xFFFF
        pos_low = position & 0xFFFF
        self.write_multiple_holdings(
            0x6200,
            8,
            [0x0001, pos_high, pos_low, velocity, self.acceleration, self.deceleration, 0x0000, 0x0010],
        )

    def set_motor_relative_position_mode(self, position: int, velocity: int = 300) -> None:
        """相对位置模式，position 单位 pulse"""
        pos_high = (position >> 16) & 0xFFFF
        pos_low = position & 0xFFFF
        self.write_multiple_holdings(
            0x6200,
            8,
            [0x0041, pos_high, pos_low, velocity, self.acceleration, self.deceleration, 0x0000, 0x0010],
        )

    def get_motor_velocity(self) -> int:
        """当前速度 rpm"""
        if self.mode == "OPEN_LOOP":
            return 0
        data = self.read_holdings(0x1046, 2)
        return _registers_to_int32(data[0], data[1])

    def get_motor_position(self) -> int:
        """当前位置 pulse"""
        data = self.read_holdings(0x602C, 2)
        return _registers_to_int32(data[0], data[1])
