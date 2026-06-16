"""配置项中文标识映射 — 含雷赛步进专用字段与界面标签"""

from __future__ import annotations

# ---------- 通用字段 ----------

FIELD_LABELS: dict[str, str] = {
    "mode": "硬件模式",
    "baudrate": "波特率",
    "timeout": "超时时间(秒)",
    "motion_timeout": "运动超时(秒)",
    "delay_read_write": "读写延时(秒)",
    "id": "设备编号",
    "slave_id": "Modbus 从站地址",
    "port": "串口路径",
    "home_position": "回零位置",
    "max_speed": "最大速度",
    "press_position": "压线位置",
    "insert_position": "插入位置",
    "tighten_steps": "收紧步数",
    "extend_timeout": "伸出超时(秒)",
    "retract_timeout": "缩回超时(秒)",
    "initial_value": "初始值",
    "open_position": "夹爪张开位置",
    "close_explosive": "夹紧炸药位置",
    "close_product": "夹紧成品位置",
    "close_detonator": "夹紧雷管位置",
    "ip": "IP 地址",
    "config_file": "途径点配置文件",
    "name": "名称",
    "description": "描述",
    "speed": "运动速度",
    "sensor_timeout": "传感器超时(秒)",
    "position": "目标位置",
    "hold_time": "保持时间(秒)",
    "steps": "步数",
    "wrap_steps": "缠膜步数",
    "cut_hold_time": "切割保持时间(秒)",
    "ready_sensor": "就绪传感器",
    "max_retries": "最大重试次数",
    "retry_delay_sec": "重试间隔(秒)",
    "step_timeout": "步骤超时(秒)",
    "auto_rollback": "失败自动回滚",
    "x": "X 坐标(m)",
    "y": "Y 坐标(m)",
    "z": "Z 坐标(m)",
    "roll": "横滚角(rad)",
    "pitch": "俯仰角(rad)",
    "yaw": "偏航角(rad)",
    "gripper_action": "夹爪动作",
    "trajectory_connect": "轨迹连接",
    "internal_name": "流程标识名",
    # 雷赛步进
    "acceleration": "加速度(ms/1000rpm)",
    "deceleration": "减速度(ms/1000rpm)",
    "pulses_per_round": "每转脉冲数",
    "encoder_resolution": "编码器分辨率",
    "peak_current": "峰值电流(0.1A)",
    "velocity": "默认速度(rpm)",
    "enable_on_connect": "连接时使能",
    "auto_home_on_init": "连接时自动回零",
    "di_neg_limit": "DI反向限位地址",
    "di_neg_limit_type": "DI反向限位类型",
    "di_pos_limit": "DI正向限位地址",
    "di_pos_limit_type": "DI正向限位类型",
    "do1": "DO1地址",
    "do1_type": "DO1类型",
    "do2": "DO2地址",
    "do2_type": "DO2类型",
    "do3": "DO3地址",
    "do3_type": "DO3类型",
    "pulse_to_distance_ratio": "脉冲/米换算比",
    "direction": "回零方向",
    "move_to_position": "回零后移动到指定位置",
    "home_mode": "回零模式",
    "single_z": "单圈Z回零",
    "current_as_home": "当前点作原点",
    "with_z_signal": "回零带Z信号",
    "ctrg": "上升沿触发",
    "software_limit": "软件限位有效",
    "power_on_home": "上电回零有效",
    "level_trigger": "电平触发有效",
}

WAYPOINT_TABLE_HEADERS = [
    "途径点名称",
    "X坐标(m)",
    "Y坐标(m)",
    "Z坐标(m)",
    "横滚(rad)",
    "俯仰(rad)",
    "偏航(rad)",
    "速度",
    "夹爪动作",
    "轨迹连接",
]

WAYPOINT_NAME_LABELS: dict[str, str] = {
    "approach_explosive": "接近取药位",
    "explosive_pick": "取炸药",
    "lift": "抬起",
    "lift_after_pick": "取药后抬起",
    "slot_approach": "接近槽位",
    "slot_place": "放入槽位",
    "retreat_from_slot": "离开槽位",
    "return_home_1": "回初始位",
    "return_home_2": "回初始位",
    "approach_product": "接近成品",
    "product_pick": "取成品",
    "lift_product": "抬起成品",
    "approach_pick": "接近取药",
    "pre_pick_open": "预取张开夹爪",
    "transit_1": "过渡点1",
    "transit_2": "过渡点2",
    "target_point": "目标点",
    "retreat_from_target": "离开目标点",
    "approach_detonator": "接近雷管",
    "detonator_pick": "取雷管",
    "lift_detonator": "抬起雷管",
    "press_wire_pass": "经过压线位",
    "winder_opening": "绕线器开口",
    "detonator_slot_place": "雷管入槽",
}

# ---------- 设备 / 分组 ----------

STEPPER_LABELS: dict[str, str] = {
    "stepper_1": "步进电机1 - 绕线器",
    "stepper_2": "步进电机2 - 压线机构",
    "stepper_3": "步进电机3 - 刀片",
    "stepper_4": "步进电机4 - 雷管插入",
    "stepper_5": "步进电机5 - 引线收紧",
}

CYLINDER_LABELS: dict[str, str] = {
    "cylinder_1": "电缸1 - 夹雷管",
    "cylinder_2": "电缸2 - 切保鲜膜",
}

SENSOR_LABELS: dict[str, str] = {
    "winder_home": "绕线器初始位传感器",
    "press_wire_ready": "压线就绪传感器",
}

GRIPPER_LABELS: dict[str, str] = {
    "left": "左臂夹爪",
    "right": "右臂夹爪",
}

ROBOT_LABELS: dict[str, str] = {
    "left_arm": "左机械臂",
    "right_arm": "右机械臂",
}

HW_MODE_LABELS: dict[str, str] = {
    "mock": "模拟模式",
    "rs485": "RS485 文本协议",
    "leadshine": "雷赛 Modbus 步进",
}

# 雷赛驱动器控制模式（leadshine_defaults.mode，非 hardware.mode）
LEADSHINE_MOTOR_MODE_LABELS: dict[str, str] = {
    "CLOSE_LOOP": "闭环控制",
    "OPEN_LOOP": "开环控制",
}

LEADSHINE_SCALAR_FIELDS = [
    "mode",
    "acceleration",
    "deceleration",
    "pulses_per_round",
    "encoder_resolution",
    "peak_current",
    "velocity",
    "di_neg_limit",
    "di_neg_limit_type",
    "di_pos_limit",
    "di_pos_limit_type",
    "do1",
    "do1_type",
    "do2",
    "do2_type",
    "do3",
    "do3_type",
    "pulse_to_distance_ratio",
]

LEADSHINE_BOOL_FIELDS = ["enable_on_connect", "auto_home_on_init"]

LEADSHINE_HOME_FIELDS = [
    "direction",
    "move_to_position",
    "home_mode",
    "single_z",
    "current_as_home",
    "with_z_signal",
]

LEADSHINE_PR_FIELDS = ["ctrg", "software_limit", "power_on_home", "level_trigger"]

# ---------- 装配步骤 ----------

STEP_LABELS: dict[str, str] = {
    "step_01_winder_home": "步骤01 - 绕线器回初始位",
    "step_03_cylinder1_retract": "步骤03 - 电缸1缩回",
    "step_05_cylinder1_extend": "步骤05 - 电缸1伸出",
    "step_06_press_wire": "步骤06 - 压线机构到位",
    "step_07_blade_press": "步骤07 - 刀片下压",
    "step_08_insert_detonator": "步骤08 - 雷管插入",
    "step_09_tighten_lead": "步骤09 - 收紧引线",
    "step_10_wrap_film": "步骤10 - 缠绕保鲜膜",
    "step_11_cut_film": "步骤11 - 切割保鲜膜",
    "step_12_press_wire_home": "步骤12 - 压线机构回零",
}

# ---------- 途径点流程 ----------

PROCESS_LABELS: dict[str, str] = {
    "home_1": "命名位姿 - 左臂初始位置1",
    "home_2": "命名位姿 - 右臂初始位置2",
    "process_pick_and_place_explosive": "流程 - 取炸药并入槽",
    "process_return_home": "流程 - 放药后回初始",
    "process_pick_product": "流程 - 取成品",
    "process_return_home_after_product": "流程 - 取成品后回初始",
    "process_left_pick_explosive": "独立流程 - 取炸药",
    "process_left_move_to_target": "独立流程 - 移至目标点",
    "process_pick_and_place_detonator": "流程 - 取雷管并入槽",
}

# ---------- 夹爪动作（界面显示中文，保存英文值）----------

GRIPPER_ACTIONS: list[tuple[str, str]] = [
    ("none", "无动作"),
    ("open", "张开夹爪"),
    ("close_explosive", "夹紧炸药"),
    ("close_product", "夹紧成品"),
    ("close_detonator", "夹紧雷管"),
]

GRIPPER_ACTION_TO_ZH: dict[str, str] = {k: v for k, v in GRIPPER_ACTIONS}
GRIPPER_ACTION_FROM_ZH: dict[str, str] = {v: k for k, v in GRIPPER_ACTIONS}

WAYPOINT_NAME_FROM_ZH: dict[str, str] = {v: k for k, v in WAYPOINT_NAME_LABELS.items()}


def field_label(key: str) -> str:
    return FIELD_LABELS.get(key, key)


def leadshine_field_label(key: str) -> str:
    """雷赛配置节字段标签（mode 与 hardware.mode 区分）"""
    if key == "mode":
        return "电机控制模式"
    return FIELD_LABELS.get(key, key)


def waypoint_display_name(name: str) -> str:
    """界面显示用中文名"""
    if not name:
        return ""
    if name in WAYPOINT_NAME_LABELS:
        return WAYPOINT_NAME_LABELS[name]
    # 已是中文或自定义名称
    if any("\u4e00" <= c <= "\u9fff" for c in name):
        return name
    return WAYPOINT_NAME_LABELS.get(name, name.replace("_", " "))


def waypoint_config_name(display: str) -> str:
    """中文显示名 → 配置文件中的 name 字段"""
    text = (display or "").strip()
    if not text:
        return text
    if text in WAYPOINT_NAME_FROM_ZH:
        return WAYPOINT_NAME_FROM_ZH[text]
    return text


def group_label(category: str, key: str) -> str:
    lookup = {
        "stepper": STEPPER_LABELS,
        "cylinder": CYLINDER_LABELS,
        "sensor": SENSOR_LABELS,
        "gripper": GRIPPER_LABELS,
        "robot": ROBOT_LABELS,
        "step": STEP_LABELS,
        "process": PROCESS_LABELS,
    }.get(category, {})
    return lookup.get(key, key)
