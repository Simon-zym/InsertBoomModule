#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InsertBoom 配置文件编辑器 (PyQt5)

启动:
    python tools/config_editor.py
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from config_editor_qt import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
