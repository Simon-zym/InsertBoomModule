"""
Modbus RTU 主机与电机寄存器读写基类
====================================

职责
----
- ModbusRtuMaster : 管理串口与 modbus_tk RtuMaster，同一路串口全局唯一实例
- MotorControl    : 对指定 slave_id 的保持/输入寄存器读写，带重试与互斥锁

线程安全
--------
同一串口上的读写通过 modbus_lock 串行化；不同串口各自独立。

急停
----
MotorControl.stop_flag / halt_writes() 可阻止后续写寄存器，不影响读操作。
"""

from __future__ import annotations

import threading
import time
from functools import wraps

import modbus_tk.modbus_rtu as modbus_rtu
import serial
from modbus_tk import defines

from hd_ware_tool.logger import Logger


def retry(max_tries=3, delay_seconds=1):
    """出错重试，超过最大重试次数后抛出异常"""

    def decorator_retry(func):
        @wraps(func)
        def wrapper_retry(*args, **kwargs):
            tries = 0
            while tries < max_tries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"{func.__name__} raised {e.__class__.__name__}. Retrying...")
                    tries += 1
                    if tries == max_tries:
                        print(f"{func.__name__} retried {max_tries} times, Failed.")
                        raise e
                    time.sleep(delay_seconds)

        return wrapper_retry

    return decorator_retry


class ModbusRtuMaster:
    """
    Modbus RTU 主机 — 按串口路径单例，支持多路独立串口。

    InsertBoom 共 5 路步进，每路一个 port，因此需要 5 个独立实例，
    而非全局唯一单例。
    """

    _instances: dict[str, ModbusRtuMaster] = {}
    _class_lock = threading.RLock()

    def __new__(cls, rtu_port_name: str, *args, **kwargs):
        with cls._class_lock:
            if rtu_port_name not in cls._instances:
                inst = super().__new__(cls)
                inst._initialized = False
                cls._instances[rtu_port_name] = inst
            return cls._instances[rtu_port_name]

    def __init__(
        self,
        rtu_port_name: str,
        baud_rate: int = 115200,
        delay_read_write: float = 0.05,
    ):
        if getattr(self, "_initialized", False):
            return

        self.port_name = rtu_port_name
        self.master = modbus_rtu.RtuMaster(
            serial.Serial(port=rtu_port_name, baudrate=baud_rate)
        )
        self.master.set_timeout(1.0)
        self.master.open()

        self.delay_read_write = delay_read_write
        self.modbus_lock = threading.Lock()
        self._initialized = True

    def close(self) -> None:
        """关闭串口并移除缓存实例"""
        with self._class_lock:
            try:
                if self.master.is_open():
                    self.master.close()
            except Exception:
                pass
            ModbusRtuMaster._instances.pop(self.port_name, None)
            self._initialized = False

    @classmethod
    def close_all(cls) -> None:
        with cls._class_lock:
            for port in list(cls._instances.keys()):
                cls._instances[port].close()


class MotorControl:
    """
    电机 Modbus 控制基类 — 封装单台从站的寄存器读写。

    子类（如 LeadShineMotorControl）在此基础上实现具体驱动器协议。
    """

    def __init__(self, master: ModbusRtuMaster, slave_id: int):
        """
        :param master: 已打开的 Modbus RTU 主机（共享同一串口）
        :param slave_id: 从站地址，对应驱动器拨码或参数
        """
        self.slave_id = slave_id
        self.modbus = master
        self.delay_read_write = master.delay_read_write
        self.stop_flag = False
        self.log = Logger(
            f"logfiles/{self.__class__.__name__}_{self.slave_id}.log",
            show_level="warning",
        )

    def halt_writes(self) -> None:
        """禁止后续写寄存器（急停用）"""
        self.stop_flag = True

    def resume_writes(self) -> None:
        self.stop_flag = False

    @retry(max_tries=3, delay_seconds=0.5)
    def read_holdings(self, address: int, count: int = 1):
        """读保持寄存器 (功能码 0x03)"""
        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 读取保持寄存器: "
            f"address:{address:#x}, count:{count}"
        )
        time.sleep(self.delay_read_write)
        with self.modbus.modbus_lock:
            try:
                result = self.modbus.master.execute(
                    slave=self.slave_id,
                    function_code=defines.READ_HOLDING_REGISTERS,
                    starting_address=address,
                    quantity_of_x=count,
                )
            except Exception as e:
                self.log.error_show(
                    f"{self.__class__.__name__}_{self.slave_id} 读取保持寄存器 "
                    f"address:{address:#x}, count:{count} 失败: {e}"
                )
                raise e
        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 读取保持寄存器结果: {result}"
        )
        return result

    @retry(max_tries=3, delay_seconds=0.5)
    def write_single_holding(self, address: int, value: int):
        """写单个保持寄存器 (功能码 0x06)"""
        if self.stop_flag:
            self.log.warn_show("电机处于停止状态，不执行写操作")
            return

        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 写单个保持寄存器: "
            f"address:{address:#x}, value:{value}"
        )
        time.sleep(self.delay_read_write)
        with self.modbus.modbus_lock:
            try:
                self.modbus.master.execute(
                    slave=self.slave_id,
                    function_code=defines.WRITE_SINGLE_REGISTER,
                    starting_address=address,
                    output_value=value,
                )
            except Exception as e:
                self.log.error_show(
                    f"{self.__class__.__name__}_{self.slave_id} 写单个保持寄存器 "
                    f"address:{address:#x}, value:{value} 失败: {e}"
                )
                raise e

    @retry(max_tries=3, delay_seconds=0.5)
    def write_multiple_holdings(self, address: int, count: int, values):
        """写多个保持寄存器 (功能码 0x10)"""
        if self.stop_flag:
            self.log.warn_show("电机处于停止状态，不执行写操作")
            return

        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 写多个保持寄存器: "
            f"address:{address:#x}, count:{count}, values:{values}"
        )
        time.sleep(self.delay_read_write)
        with self.modbus.modbus_lock:
            try:
                self.modbus.master.execute(
                    slave=self.slave_id,
                    function_code=defines.WRITE_MULTIPLE_REGISTERS,
                    starting_address=address,
                    quantity_of_x=count,
                    output_value=values,
                )
            except Exception as e:
                self.log.error_show(
                    f"{self.__class__.__name__}_{self.slave_id} 写多个保持寄存器 "
                    f"address:{address:#x}, count:{count}, values:{values} 失败: {e}"
                )
                raise e

    @retry(max_tries=3, delay_seconds=0.5)
    def read_input_registers(self, address: int, count: int = 1):
        """读输入寄存器 (功能码 0x04)"""
        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 读取输入寄存器: "
            f"address:{address:#x}, count:{count}"
        )
        time.sleep(self.delay_read_write)
        with self.modbus.modbus_lock:
            try:
                result = self.modbus.master.execute(
                    slave=self.slave_id,
                    function_code=defines.READ_INPUT_REGISTERS,
                    starting_address=address,
                    quantity_of_x=count,
                )
            except Exception as e:
                self.log.error_show(
                    f"{self.__class__.__name__}_{self.slave_id} 读取输入寄存器 "
                    f"address:{address:#x}, count:{count} 失败: {e}"
                )
                raise e
        self.log.info_show(
            f"{self.__class__.__name__}_{self.slave_id} 读取输入寄存器结果: {result}"
        )
        return result
