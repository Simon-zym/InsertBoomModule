"""
雷赛步进电机 Modbus RTU 控制库
================================

目录结构
--------
modbus_motor_ctl.py     Modbus RTU 主机 + 寄存器读写基类
leadshine_motor_ctl.py  雷赛驱动器 PR 模式高层接口
test_leadshine_motor_ctl.py  初始化流程与米/脉冲换算示例
logger.py               日志（读写寄存器时输出）

依赖
----
    pip install modbus-tk pyserial

快速上手
--------
    from hd_ware_tool.modbus_motor_ctl import ModbusRtuMaster
    from hd_ware_tool.leadshine_motor_ctl import LeadShineMotorControl

    master = ModbusRtuMaster("/dev/ttyUSB0", baud_rate=115200)
    motor = LeadShineMotorControl(master, slave_id=1)
    motor.set_pulses_per_round(10000)
    motor.set_motor_mode("CLOSE_LOOP")
    motor.set_motor_absolute_position_mode(5000, velocity=300)
    motor.wait_until_motor_stop(timeout=30)
    master.close()

与 InsertBoom 集成
------------------
主程序在 system.yaml 中设置 hardware.mode: leadshine，
由 insert_boom/hardware/leadshine_devices.py 读取配置并调用本库。

配置编辑器
----------
python tools/config_editor.py → 系统硬件 → 「雷赛步进 (全局)」/「雷赛步进 (调试)」

注意事项
--------
1. ModbusRtuMaster 按串口路径单例，5 路电机需 5 个不同 port
2. 寄存器地址为驱动器手册中的协议地址（modbus_tk 直接使用）
3. DI/DO 地址在 yaml 中以十进制保存，注释中标注了十六进制对照
4. 接线：光电开关黑线接 DI，棕正蓝负，COM 接 24V
"""

from hd_ware_tool.leadshine_motor_ctl import LeadShineMotorControl
from hd_ware_tool.modbus_motor_ctl import ModbusRtuMaster, MotorControl

__all__ = ["LeadShineMotorControl", "ModbusRtuMaster", "MotorControl"]
