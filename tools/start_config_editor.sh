#!/usr/bin/env bash
# 启动 InsertBoom PyQt 配置编辑器
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 tools/config_editor.py "$@"
