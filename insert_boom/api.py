"""
InsertBoom 外部调用接口

用法:
    from insert_boom import InsertBoomService, FlowType, RunResult

    service = InsertBoomService(hw_mode="mock", robot_mode="mock")
    service.connect()

    # 完整装配
    result = service.run(FlowType.ASSEMBLY)

    # 左臂独立：取炸药 → 目标点
    result = service.run("left_pick_transfer")

    service.disconnect()
    print(result.success, result.message)
"""

from __future__ import annotations

from typing import Callable, Optional, Union

from insert_boom.config_loader import load_yaml
from insert_boom.core.context import WorkflowContext
from insert_boom.core.events import WorkflowEvent
from insert_boom.core.flow_lock import FlowLock
from insert_boom.core.flow_types import (
    FLOW_DESCRIPTIONS,
    FlowType,
    RunResult,
    parse_flow_type,
)
from insert_boom.flows.assembly_flow import run_assembly_flow
from insert_boom.flows.left_pick_transfer_flow import run_left_pick_transfer_flow
from insert_boom.hardware.hardware_manager import HardwareManager
from insert_boom.hardware.mock_devices import MockSensor
from insert_boom.log_helper import get_logger
from insert_boom.robot.arm_left import LeftArm
from insert_boom.robot.arm_right import RightArm

logger = get_logger("api")

# 流程类型 → 执行函数
_FLOW_RUNNERS = {
    FlowType.ASSEMBLY: lambda ctx, **kw: run_assembly_flow(
        ctx, start_from=kw.get("start_from", 0)
    ),
    FlowType.LEFT_PICK_TRANSFER: lambda ctx, **kw: run_left_pick_transfer_flow(ctx),
}


class InsertBoomService:
    """
    InsertBoom 服务 — 供外部程序调用的统一入口

    特性:
        - 输入流程类型，返回 RunResult
        - 同一时刻只能执行一种流程（互斥锁）
        - 支持长连接（connect 一次，多次 run）
    """

    def __init__(
        self,
        hw_mode: str = "mock",
        robot_mode: str = "mock",
        system_config: Optional[dict] = None,
        workflow_config: Optional[dict] = None,
    ):
        self.hw_mode = hw_mode
        self.robot_mode = robot_mode
        self.system_config = system_config
        self.workflow_config = workflow_config
        self.ctx: Optional[WorkflowContext] = None
        self._connected = False
        self._flow_lock = FlowLock()
        self._event_listeners: list[Callable[[WorkflowEvent], None]] = []

    def add_event_listener(self, listener: Callable[[WorkflowEvent], None]) -> None:
        """注册事件监听（日志、UI 等）"""
        self._event_listeners.append(listener)
        if self.ctx is not None:
            self.ctx.event_listeners.append(listener)

    def connect(self, winder_blocked: bool = False) -> bool:
        """
        连接硬件和机械臂（长连接，可多次 run）

        Returns:
            True 表示连接成功
        """
        if self._connected:
            logger.info("服务已连接，跳过重复连接")
            return True

        if self.system_config is None:
            self.system_config = load_yaml("config/system.yaml")
        if self.workflow_config is None:
            self.workflow_config = load_yaml("config/workflow.yaml")

        self.system_config.setdefault("hardware", {})["mode"] = self.hw_mode

        self.ctx = WorkflowContext(
            system_config=self.system_config,
            workflow_config=self.workflow_config,
        )
        for listener in self._event_listeners:
            self.ctx.event_listeners.append(listener)

        hw = HardwareManager(self.system_config)
        if not hw.connect_all():
            logger.error("硬件连接失败")
            self.ctx = None
            return False

        if winder_blocked:
            sensor = hw.sensors.get("winder_home")
            if isinstance(sensor, MockSensor):
                sensor.set_value(True)

        self.ctx.hw = hw

        left = LeftArm(self.system_config, mode=self.robot_mode)
        right = RightArm(self.system_config, mode=self.robot_mode)
        ok_l, msg_l = left.connect()
        if not ok_l:
            logger.error("左臂连接失败: %s", msg_l)
            hw.disconnect_all()
            self.ctx = None
            return False
        ok_r, msg_r = right.connect()
        if not ok_r:
            logger.error("右臂连接失败: %s", msg_r)
            left.disconnect()
            hw.disconnect_all()
            self.ctx = None
            return False

        self.ctx.left_arm = left
        self.ctx.right_arm = right
        self._connected = True
        logger.info("InsertBoomService 已连接 (hw=%s, robot=%s)", self.hw_mode, self.robot_mode)
        return True

    def disconnect(self) -> None:
        """断开所有设备"""
        if self.ctx is None:
            return
        if self.ctx.left_arm:
            self.ctx.left_arm.disconnect()
        if self.ctx.right_arm:
            self.ctx.right_arm.disconnect()
        if self.ctx.hw:
            self.ctx.hw.disconnect_all()
        self.ctx = None
        self._connected = False
        logger.info("InsertBoomService 已断开")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def is_running(self) -> bool:
        return self._flow_lock.is_busy()

    def get_current_flow(self) -> Optional[str]:
        current = self._flow_lock.get_current()
        return current.value if current else None

    def list_flow_types(self) -> dict[str, str]:
        """列出所有可用流程类型及说明"""
        return {ft.value: FLOW_DESCRIPTIONS[ft] for ft in FlowType}

    def run(
        self,
        flow_type: Union[FlowType, str],
        start_from: int = 0,
        auto_connect: bool = True,
    ) -> RunResult:
        """
        执行指定流程（外部主入口）

        Args:
            flow_type: 流程类型，如 FlowType.ASSEMBLY 或 "left_pick_transfer"
            start_from: 仅 assembly 有效，从指定 Step 开始
            auto_connect: 未连接时是否自动 connect

        Returns:
            RunResult(success, flow_type, message, failed_step)
        """
        try:
            ft = flow_type if isinstance(flow_type, FlowType) else parse_flow_type(flow_type)
        except ValueError as exc:
            return RunResult(False, str(flow_type), str(exc))

        if not self._connected:
            if not auto_connect:
                return RunResult(False, ft.value, "服务未连接，请先调用 connect()")
            if not self.connect():
                return RunResult(False, ft.value, "自动连接失败")

        if not self._flow_lock.acquire(ft):
            busy = self._flow_lock.get_current()
            busy_name = busy.value if busy else "unknown"
            msg = f"已有流程 '{busy_name}' 正在运行，同一时刻只能执行一种流程"
            logger.warning(msg)
            return RunResult(False, ft.value, msg)

        assert self.ctx is not None
        try:
            runner = _FLOW_RUNNERS[ft]
            return runner(self.ctx, start_from=start_from)
        finally:
            self._flow_lock.release(ft)

    def stop(self) -> None:
        """急停当前流程"""
        if self.ctx is not None:
            self.ctx.request_abort()

    def __enter__(self) -> "InsertBoomService":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()


def run_flow(
    flow_type: Union[FlowType, str],
    hw_mode: str = "mock",
    robot_mode: str = "mock",
    start_from: int = 0,
) -> RunResult:
    """
    一次性执行流程（自动 connect / disconnect）

    适合脚本或外部程序单次调用:
        result = run_flow("left_pick_transfer")
        if result.success:
            ...
    """
    with InsertBoomService(hw_mode=hw_mode, robot_mode=robot_mode) as service:
        return service.run(flow_type, start_from=start_from, auto_connect=False)
