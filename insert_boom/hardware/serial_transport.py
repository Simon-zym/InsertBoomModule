"""
RS485 串口传输层 — 5 路步进 + 2 路电缸各自独立串口

每路设备独占一个 serial.Serial 实例，避免总线冲突。
收发耗时在 write_read / write_read_line 中打印，便于排查虚拟串口延迟。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from insert_boom.log_helper import get_logger

logger = get_logger("hardware.serial")

try:
    import serial
except ImportError:
    serial = None  # type: ignore


class SerialTransport:
    """单路 RS485 串口封装（线程安全）"""

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 0.5,
        device_name: str = "",
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.device_name = device_name or port
        self._ser: Optional["serial.Serial"] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        if serial is None:
            logger.error("pyserial 未安装，请执行: pip install pyserial")
            return False
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                xonxoff=False,
                rtscts=False,
            )
            logger.info("[%s] RS485 已连接 %s @ %d", self.device_name, self.port, self.baudrate)
            return True
        except Exception as exc:
            logger.error("[%s] RS485 连接失败 %s: %s", self.device_name, self.port, exc)
            return False

    def disconnect(self) -> None:
        with self._lock:
            if self._ser and self._ser.is_open:
                self._ser.close()
            self._ser = None

    @property
    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def write(self, data: bytes) -> bool:
        with self._lock:
            if not self.is_connected:
                return False
            try:
                t0 = time.perf_counter()
                self._ser.reset_input_buffer()
                self._ser.write(data)
                send_ms = (time.perf_counter() - t0) * 1000
                logger.debug(
                    "[%s] 发送完成 %.2fms, %d bytes",
                    self.device_name,
                    send_ms,
                    len(data),
                )
                return True
            except Exception as exc:
                logger.error("[%s] 写入失败: %s", self.device_name, exc)
                return False

    def write_read(self, data: bytes, read_len: int = 64, read_timeout: Optional[float] = None) -> Optional[bytes]:
        """
        发送并读取应答

        打印:
            - 发送耗时（write 完成）
            - 等待响应耗时（write 结束 → read 返回）
            - 往返总耗时
        """
        with self._lock:
            if not self.is_connected:
                return None
            cmd_preview = data.decode("ascii", errors="ignore").strip()
            try:
                t_total = time.perf_counter()

                t_send = time.perf_counter()
                self._ser.reset_input_buffer()
                self._ser.write(data)
                send_ms = (time.perf_counter() - t_send) * 1000

                t_read = time.perf_counter()
                # 优先读到行尾，避免 read(128) 在虚拟串口上傻等满超时
                if hasattr(self._ser, "read_until"):
                    resp = self._ser.read_until(expected=b"\n", size=read_len)
                else:
                    resp = self._ser.read(read_len)
                read_ms = (time.perf_counter() - t_read) * 1000
                total_ms = (time.perf_counter() - t_total) * 1000

                resp_preview = resp.decode("ascii", errors="ignore").strip() if resp else ""
                effective_timeout = read_timeout if read_timeout is not None else self.timeout

                if resp:
                    logger.info(
                        "[%s] 串口 >> %s | 发送 %.2fms | 等响应 %.2fms | 总计 %.2fms | << %s",
                        self.device_name,
                        cmd_preview,
                        send_ms,
                        read_ms,
                        total_ms,
                        resp_preview,
                    )
                else:
                    logger.warning(
                        "[%s] 串口 >> %s | 发送 %.2fms | 等响应 %.2fms | 总计 %.2fms | << (无应答, 超时=%.1fs)",
                        self.device_name,
                        cmd_preview,
                        send_ms,
                        read_ms,
                        total_ms,
                        effective_timeout,
                    )

                return resp if resp else None
            except Exception as exc:
                logger.error("[%s] 读写失败 [%s]: %s", self.device_name, cmd_preview, exc)
                return None

    def write_line(self, cmd: str) -> bool:
        return self.write((cmd.strip() + "\r\n").encode("ascii"))

    def write_read_line(self, cmd: str, timeout: float = 1.0) -> Optional[str]:
        old_timeout = self.timeout
        self.timeout = timeout
        if self._ser:
            self._ser.timeout = timeout
        resp = self.write_read(
            (cmd.strip() + "\r\n").encode("ascii"),
            read_len=128,
            read_timeout=timeout,
        )
        self.timeout = old_timeout
        if self._ser:
            self._ser.timeout = old_timeout
        if resp is None:
            return None
        return resp.decode("ascii", errors="ignore").strip()
