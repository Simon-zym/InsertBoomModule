#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RS485 虚拟设备应答器 — 配合 InsertBoom 的 rs485 模式使用

作用:
    在「模拟器侧」串口上监听 InsertBoom 发来的文本命令，并按协议自动回复。
    不修改 InsertBoom 主程序，单独运行本脚本即可。

串口配对（需先用 setup_virtual_serial.sh 创建）:
    InsertBoom 连接(偶数)     本脚本连接(奇数)      对应设备
    /dev/ttyVUSB0      <->   /dev/ttyVUSB1       stepper_1 绕线器
    /dev/ttyVUSB2      <->   /dev/ttyVUSB3       stepper_2 压线
    /dev/ttyVUSB4      <->   /dev/ttyVUSB5       stepper_3 刀片
    /dev/ttyVUSB6      <->   /dev/ttyVUSB7       stepper_4 雷管插入
    /dev/ttyVUSB8      <->   /dev/ttyVUSB9       stepper_5 收紧引线
    /dev/ttyVUSB10     <->   /dev/ttyVUSB11      cylinder_1 电缸1
    /dev/ttyVUSB12     <->   /dev/ttyVUSB13      cylinder_2 电缸2

协议（与 insert_boom/hardware/rs485_devices.py 一致）:
    步进: MOVE_ABS:<pos>,<speed> | MOVE_REL:<steps>,<speed> | HOME:<speed> | STOP | POS?
    电缸: EXTEND | RETRACT | STOP | STATUS?
    应答: OK | POS:<n> | STATUS:EXTENDED | STATUS:RETRACTED

用法:
    # 1. 先创建虚拟串口
    sudo bash tools/setup_virtual_serial.sh

    # 2. 启动本应答器（保持运行）
    python3 tools/rs485_virtual_responder.py

    # 3. 另开终端跑 InsertBoom（机械臂用 mock）
    python -m insert_boom.main --hw-mode rs485 --robot-mode mock -v
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import serial
except ImportError:
    print("请先安装 pyserial: pip install pyserial")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置 — 7 路模拟器端口（奇数），与 InsertBoom 的偶数端口一一配对
# ---------------------------------------------------------------------------
BAUDRATE = 115200

SIMULATOR_PORTS: List[dict] = [
    {"port": "/dev/ttyVUSB1",  "name": "stepper_1",  "type": "stepper"},
    {"port": "/dev/ttyVUSB3",  "name": "stepper_2",  "type": "stepper"},
    {"port": "/dev/ttyVUSB5",  "name": "stepper_3",  "type": "stepper"},
    {"port": "/dev/ttyVUSB7",  "name": "stepper_4",  "type": "stepper"},
    {"port": "/dev/ttyVUSB9",  "name": "stepper_5",  "type": "stepper"},
    {"port": "/dev/ttyVUSB11", "name": "cylinder_1", "type": "cylinder"},
    {"port": "/dev/ttyVUSB13", "name": "cylinder_2", "type": "cylinder"},
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rs485_sim")


@dataclass
class StepperState:
    """步进电机模拟状态"""

    position: int = 0
    home_position: int = 0


@dataclass
class CylinderState:
    """电缸模拟状态 — False=缩回 RETRACTED, True=伸出 EXTENDED"""

    extended: bool = False


@dataclass
class PortWorker:
    """单路串口工作线程"""

    port: str
    name: str
    device_type: str
    stepper: StepperState = field(default_factory=StepperState)
    cylinder: CylinderState = field(default_factory=CylinderState)
    _stop: threading.Event = field(default_factory=threading.Event)
    _thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()

    def _open_serial(self) -> serial.Serial:
        return serial.Serial(
            port=self.port,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
            xonxoff=False,
            rtscts=False,
        )

    def _reply(self, ser: serial.Serial, text: str) -> None:
        """发送应答行（必须以 \\r\\n 结尾，与 InsertBoom 一致）"""
        data = (text.strip() + "\r\n").encode("ascii")
        ser.write(data)
        log.info("[%s] << %s", self.name, text)

    def _handle_stepper(self, cmd: str) -> str:
        if cmd == "STOP":
            return "OK"
        if cmd == "POS?":
            return f"POS:{self.stepper.position}"
        if cmd.startswith("HOME:"):
            self.stepper.position = self.stepper.home_position
            return "OK"
        if cmd.startswith("MOVE_ABS:"):
            # 格式: MOVE_ABS:5000,300
            try:
                body = cmd.split(":", 1)[1]
                pos_str, _speed = body.split(",", 1)
                self.stepper.position = int(pos_str)
            except (ValueError, IndexError):
                return "ERR:bad_format"
            return "OK"
        if cmd.startswith("MOVE_REL:"):
            try:
                body = cmd.split(":", 1)[1]
                steps_str, _speed = body.split(",", 1)
                self.stepper.position += int(steps_str)
            except (ValueError, IndexError):
                return "ERR:bad_format"
            return "OK"
        return "ERR:unknown_cmd"

    def _handle_cylinder(self, cmd: str) -> str:
        if cmd == "STOP":
            return "OK"
        if cmd == "EXTEND":
            self.cylinder.extended = True
            return "OK"
        if cmd == "RETRACT":
            self.cylinder.extended = False
            return "OK"
        if cmd == "STATUS?":
            if self.cylinder.extended:
                return "STATUS:EXTENDED"
            return "STATUS:RETRACTED"
        return "ERR:unknown_cmd"

    def _dispatch(self, cmd: str) -> str:
        cmd = cmd.strip()
        if not cmd:
            return ""
        log.info("[%s] >> %s", self.name, cmd)
        if self.device_type == "stepper":
            return self._handle_stepper(cmd)
        return self._handle_cylinder(cmd)

    def _run(self) -> None:
        """主循环: 读一行命令 → 回一行应答"""
        while not self._stop.is_set():
            ser = None
            try:
                ser = self._open_serial()
                log.info("[%s] 已打开 %s，等待 InsertBoom 命令...", self.name, self.port)
                buffer = b""

                while not self._stop.is_set():
                    chunk = ser.read(64)
                    if not chunk:
                        continue
                    buffer += chunk

                    # 按行解析（支持 \r\n 或 \n）
                    while b"\n" in buffer or b"\r" in buffer:
                        for sep in (b"\r\n", b"\n", b"\r"):
                            if sep in buffer:
                                line, _, buffer = buffer.partition(sep)
                                break
                        else:
                            break

                        try:
                            cmd = line.decode("ascii", errors="ignore").strip()
                        except Exception:
                            continue
                        if not cmd:
                            continue

                        resp = self._dispatch(cmd)
                        if resp:
                            self._reply(ser, resp)

            except serial.SerialException as exc:
                log.warning("[%s] 串口异常 %s: %s — 3s 后重连", self.name, self.port, exc)
                time.sleep(3.0)
            except Exception as exc:
                log.error("[%s] 未知错误: %s — 3s 后重连", self.name, exc)
                time.sleep(3.0)
            finally:
                if ser and ser.is_open:
                    ser.close()


def main() -> None:
    log.info("=" * 60)
    log.info("RS485 虚拟设备应答器启动")
    log.info("监听端口（模拟器侧，奇数）:")
    for item in SIMULATOR_PORTS:
        log.info("  %s  %s  [%s]", item["port"], item["name"], item["type"])
    log.info("请确认 InsertBoom 的 system.yaml 已改为偶数端口 ttyVUSB0~12")
    log.info("=" * 60)

    workers: List[PortWorker] = []
    for item in SIMULATOR_PORTS:
        w = PortWorker(port=item["port"], name=item["name"], device_type=item["type"])
        w.start()
        workers.append(w)

    log.info("全部 %d 路应答线程已启动，按 Ctrl+C 退出", len(workers))
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        log.info("正在停止...")
        for w in workers:
            w.stop()


if __name__ == "__main__":
    main()
