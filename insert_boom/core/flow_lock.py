"""
流程互斥锁 — 保证同一时刻只运行一种流程
"""

from __future__ import annotations

import threading
from typing import Optional

from insert_boom.core.flow_types import FlowType


class FlowLock:
    """全局流程锁（单例）"""

    _instance: Optional["FlowLock"] = None
    _singleton_guard = threading.Lock()

    def __new__(cls) -> "FlowLock":
        with cls._singleton_guard:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._lock = threading.Lock()
                inst._current_flow: Optional[FlowType] = None
                cls._instance = inst
            return cls._instance

    def acquire(self, flow_type: FlowType) -> bool:
        """
        尝试占用流程锁

        Returns:
            True  — 成功获取，可以执行
            False — 已有其他流程在运行
        """
        with self._lock:
            if self._current_flow is not None:
                return False
            self._current_flow = flow_type
            return True

    def release(self, flow_type: FlowType) -> None:
        """释放流程锁"""
        with self._lock:
            if self._current_flow == flow_type:
                self._current_flow = None

    def get_current(self) -> Optional[FlowType]:
        with self._lock:
            return self._current_flow

    def is_busy(self) -> bool:
        return self.get_current() is not None
