"""InsertBoom 统一异常定义"""


class InsertBoomError(Exception):
    """流程基础异常"""

    def __init__(self, message: str, step_index: int = -1):
        self.step_index = step_index
        super().__init__(message)


class PreCheckError(InsertBoomError):
    """步骤前置条件不满足"""


class ExecutionError(InsertBoomError):
    """步骤执行失败"""


class PostCheckError(InsertBoomError):
    """步骤后置确认失败"""


class HardwareError(InsertBoomError):
    """硬件通信或动作失败"""


class RobotError(InsertBoomError):
    """机械臂控制失败"""


class WorkflowAborted(InsertBoomError):
    """流程被用户中止（急停/停止）"""
