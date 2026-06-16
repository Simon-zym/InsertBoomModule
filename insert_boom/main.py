#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InsertBoom 装配流程 — 程序入口

启动后做的事:
    1. 读取 config/ 下的 YAML 配置
    2. 连接硬件（5步进 + 2电缸 + 传感器）和双臂
    3. 按指定流程类型执行（assembly 或 left_pick_transfer）

常用命令:
    python -m insert_boom.main                                    # Mock 完整装配
    python -m insert_boom.main --flow-type left_pick_transfer     # 左臂独立取药流程
    python -m insert_boom.main --hw-mode rs485                    # 真实 RS485 硬件
    python -m insert_boom.main --robot-mode real                  # 真实机械臂
    python -m insert_boom.main --start-from 6                   # 从第6步开始调试
    python -m insert_boom.main -v                                 # 显示更详细的 DEBUG 日志
"""

from __future__ import annotations

import argparse
import logging
import sys

from insert_boom.api import InsertBoomService
from insert_boom.core.events import EventType, WorkflowEvent
from insert_boom.core.flow_types import FlowType, parse_flow_type
from insert_boom.log_helper import get_logger

logger = get_logger("main")


def setup_logging(verbose: bool = False) -> None:
    """配置日志格式 — 默认 INFO，-v 时显示 DEBUG"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def console_event_listener(event: WorkflowEvent) -> None:
    """
    控制台事件监听 — 把关键进度打印到终端

    LOG 类型 → 直接打印步骤日志
    其他类型 → 带 >>> 前缀的进度提示
    """
    if event.event_type == EventType.LOG:
        print(event.message)
    elif event.event_type in (
        EventType.STEP_STARTED,
        EventType.STEP_COMPLETED,
        EventType.WORKFLOW_STARTED,
        EventType.WORKFLOW_COMPLETED,
        EventType.WORKFLOW_ERROR,
        EventType.WORKFLOW_ABORTED,
    ):
        print(f"\n>>> {event.message}")


def run_workflow(
    flow_type: str = "assembly",
    start_from: int = 0,
    hw_mode: str = "mock",
    robot_mode: str = "mock",
    winder_blocked: bool = False,
) -> int:
    """执行指定流程，返回进程退出码（0=成功）"""
    service = InsertBoomService(hw_mode=hw_mode, robot_mode=robot_mode)
    service.add_event_listener(console_event_listener)

    try:
        ft = parse_flow_type(flow_type)
        if not service.connect(winder_blocked=winder_blocked):
            print("\n连接失败，请检查硬件/机械臂配置")
            return 2

        result = service.run(ft, start_from=start_from, auto_connect=False)

        if result.success:
            print("\n" + "=" * 50)
            print(f"流程 [{result.flow_type}] SUCCESS: {result.message}")
            print("=" * 50)
            return 0

        print("\n" + "=" * 50)
        if result.failed_step >= 0:
            print(
                f"流程 [{result.flow_type}] FAILED: {result.message} "
                f"(Step {result.failed_step})"
            )
        else:
            print(f"流程 [{result.flow_type}] FAILED: {result.message}")
        print("=" * 50)
        return 1

    except KeyboardInterrupt:
        logger.warning("用户按 Ctrl+C 中断")
        print("\n用户中断")
        service.stop()
        return 130

    except Exception as exc:
        logger.exception("程序异常: %s", exc)
        return 2

    finally:
        service.disconnect()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="InsertBoom 自动化装配流程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--flow-type",
        default="assembly",
        help="流程类型: assembly=完整装配, left_pick_transfer=左臂取药并移至目标点",
    )
    parser.add_argument("--start-from", type=int, default=0, help="从指定步骤开始 (0-13，仅 assembly)")
    parser.add_argument(
        "--hw-mode",
        choices=["mock", "rs485"],
        default="mock",
        help="硬件模式: mock=模拟, rs485=7路独立RS485串口",
    )
    parser.add_argument(
        "--robot-mode",
        choices=["mock", "real"],
        default="mock",
        help="机械臂模式: mock=模拟, real=RealMan SDK",
    )
    parser.add_argument(
        "--winder-blocked",
        action="store_true",
        help="测试用: 模拟绕线器传感器遮挡",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="显示 DEBUG 详细日志")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)
    sys.exit(
        run_workflow(
            flow_type=args.flow_type,
            start_from=args.start_from,
            hw_mode=args.hw_mode,
            robot_mode=args.robot_mode,
            winder_blocked=args.winder_blocked,
        )
    )


if __name__ == "__main__":
    main()
