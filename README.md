# InsertBoom 自动化装配系统

RealMan 双臂 + 步进电机 + 电缸协同的炸药/雷管装配流程控制。

## 硬件拓扑

| 设备 | 数量 | 通信 | 固定配置 |
|------|------|------|----------|
| 左机械臂 | 1 | TCP API | **172.16.0.89:8080** |
| 右机械臂 | 1 | TCP API | **172.16.0.88:8080** |
| 步进电机 | 5 | 各 1 路 RS485 | `/dev/ttyUSB0` ~ `ttyUSB4` |
| 电缸 | 2 | 各 1 路 RS485 | `/dev/ttyUSB5` ~ `ttyUSB6` |

步进电机映射：

| 逻辑名 | 图标 | 串口（默认） | 用途 |
|--------|------|-------------|------|
| stepper_1 | 图标1 | ttyUSB0 | 绕线器 |
| stepper_2 | 图标5 | ttyUSB1 | 压线机构 |
| stepper_3 | 图标2 | ttyUSB2 | 刀片 |
| stepper_4 | 图标3 | ttyUSB3 | 雷管插入 |
| stepper_5 | 图标4 | ttyUSB4 | 引线收紧 |
| cylinder_1 | — | ttyUSB5 | 夹雷管电缸 |
| cylinder_2 | — | ttyUSB6 | 切膜电缸 |

## 途径点配置（拆分独立流程）

### 左臂 `config/waypoints_left.yaml`

| 流程键名 | 说明 |
|----------|------|
| `process_pick_and_place_explosive` | 运动到取药位 → 夹取炸药 → 途径点入炸药槽 |
| `process_return_home` | 放药后回初始位置1 |
| `process_pick_product` | 取成品途径 |
| `process_return_home_after_product` | 取成品后回初始 |

### 右臂 `config/waypoints_right.yaml`

| 流程键名 | 说明 |
|----------|------|
| `process_pick_and_place_detonator` | 取雷管 → 压线位 → 绕线器开口 → 入雷管槽 |
| `process_return_home` | 放雷管后回初始位置2 |

## 快速开始

```bash
cd InsertBoomModule
pip install -r requirements.txt

# Mock 模式（无需硬件）
python -m insert_boom.main

# RS485 真实步进/电缸（需接好 7 路串口）
python -m insert_boom.main --hw-mode rs485

# 真实双臂
python -m insert_boom.main --robot-mode real

# 组合：RS485 硬件 + 真实机械臂
python -m insert_boom.main --hw-mode rs485 --robot-mode real

# 从指定步骤调试
python -m insert_boom.main --start-from 6
```

## 项目结构

```
InsertBoomModule/
├── config/
│   ├── system.yaml           # IP、7路串口、步进参数
│   ├── workflow.yaml         # 流程超时/重试
│   ├── waypoints_left.yaml   # 左臂途径点（拆分流程）
│   └── waypoints_right.yaml  # 右臂途径点（拆分流程）
├── insert_boom/
│   ├── core/                 # 流程引擎
│   ├── hardware/
│   │   ├── serial_transport.py  # RS485 串口层
│   │   ├── rs485_devices.py     # 步进/电缸 RS485 驱动
│   │   └── mock_devices.py      # Mock 驱动
│   ├── robot/
│   │   ├── constants.py      # 固定 IP
│   │   ├── arm_left.py       # 左臂 172.16.0.89
│   │   └── arm_right.py      # 右臂 172.16.0.88
│   ├── steps/                # Step 0-13
│   └── main.py
└── TestRealmanCanFD1.py      # 原 CanFD demo（保留）
```

## RS485 协议（可定制）

步进电机命令（`rs485_devices.py`）：

```
MOVE_ABS:<position>,<speed>
MOVE_REL:<steps>,<speed>
HOME:<speed>
STOP
POS?
```

电缸命令：

```
EXTEND / RETRACT / STOP / STATUS?
```

应答：`OK` / `ERR:<code>` / `POS:<n>` / `STATUS:EXTENDED|RETRACTED`

若现场控制器协议不同，修改 `insert_boom/hardware/rs485_devices.py` 中的命令格式即可。

## 配置修改

1. **串口路径** — 编辑 `config/system.yaml` 中各设备 `port`
2. **途径点坐标** — 示教后更新 `waypoints_left.yaml` / `waypoints_right.yaml`
3. **步进位置** — `system.yaml` 中 `press_position`、`insert_position` 等

## 安全提示

- 首次真机前用 Mock 验证流程顺序
- 途径点逐点低速示教
- `auto_rollback: false`，失败后人工介入
