"""InsertBoom 自动化装配流程包"""

from insert_boom.api import InsertBoomService, run_flow
from insert_boom.core.flow_types import FlowType, RunResult

__version__ = "0.1.0"

__all__ = [
    "InsertBoomService",
    "run_flow",
    "FlowType",
    "RunResult",
    "__version__",
]
