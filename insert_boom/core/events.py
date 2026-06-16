"""流程事件定义 — 用于日志、UI 回调、状态监控"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class WorkflowState(Enum):
    """流程全局状态"""

    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()
    ABORTED = auto()


class EventType(Enum):
    """事件类型"""

    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()
    WORKFLOW_ABORTED = auto()
    STEP_STARTED = auto()
    STEP_COMPLETED = auto()
    STEP_FAILED = auto()
    HARDWARE_ACTION = auto()
    ROBOT_ACTION = auto()
    SENSOR_READ = auto()
    LOG = auto()


@dataclass
class WorkflowEvent:
    """流程事件载体"""

    event_type: EventType
    message: str
    step_index: int = -1
    step_name: str = ""
    data: Optional[Any] = None
