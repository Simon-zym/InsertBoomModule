#!/bin/bash
# ============================================================================
# 创建 7 对虚拟串口 /dev/ttyVUSB0 ~ /dev/ttyVUSB13
#
# 偶数端口 (0,2,4,6,8,10,12) → InsertBoom 程序连接
# 奇数端口 (1,3,5,7,9,11,13)  → rs485_virtual_responder.py 连接
#
# 用法:
#   sudo bash tools/setup_virtual_serial.sh        # 创建
#   sudo bash tools/setup_virtual_serial.sh stop   # 停止
# ============================================================================

set -e

PID_FILE="/tmp/insert_boom_socat.pid"
LOG_DIR="/tmp/insert_boom_socat_logs"

create_pair() {
    local even=$1   # InsertBoom 用
    local odd=$2    # 应答器用
    local logfile="${LOG_DIR}/socat_${even}_${odd}.log"

    # 若已存在先删掉旧链接
    rm -f "/dev/${even}" "/dev/${odd}" 2>/dev/null || true

    socat -d -d \
        "pty,link=/dev/${even},raw,echo=0,mode=666" \
        "pty,link=/dev/${odd},raw,echo=0,mode=666" \
        >> "$logfile" 2>&1 &

    echo $! >> "$PID_FILE"
    echo "  已创建配对: /dev/${even} <-> /dev/${odd}  (pid $!)"
}

stop_all() {
    if [ -f "$PID_FILE" ]; then
        echo "停止 socat 进程..."
        while read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    pkill -f "socat.*ttyVUSB" 2>/dev/null || true
    rm -f /dev/ttyVUSB{0..13} 2>/dev/null || true
    echo "已停止并清理虚拟串口"
    exit 0
}

if [ "$1" = "stop" ]; then
    stop_all
fi

if [ "$(id -u)" != "0" ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

if ! command -v socat >/dev/null 2>&1; then
    echo "请先安装 socat: sudo apt install socat"
    exit 1
fi

mkdir -p "$LOG_DIR"
rm -f "$PID_FILE"
touch "$PID_FILE"

echo "创建 7 对虚拟串口..."
create_pair ttyVUSB0  ttyVUSB1    # stepper_1
create_pair ttyVUSB2  ttyVUSB3    # stepper_2
create_pair ttyVUSB4  ttyVUSB5    # stepper_3
create_pair ttyVUSB6  ttyVUSB7    # stepper_4
create_pair ttyVUSB8  ttyVUSB9    # stepper_5
create_pair ttyVUSB10 ttyVUSB11   # cylinder_1
create_pair ttyVUSB12 ttyVUSB13   # cylinder_2

sleep 0.5
echo ""
echo "验证端口:"
ls -l /dev/ttyVUSB* 2>/dev/null || echo "  警告: 部分端口未创建成功，请查看 ${LOG_DIR}/"
echo ""
echo "完成。下一步:"
echo "  1. python3 tools/rs485_virtual_responder.py"
echo "  2. python -m insert_boom.main --hw-mode rs485 --robot-mode mock"
