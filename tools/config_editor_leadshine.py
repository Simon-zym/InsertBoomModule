"""
配置编辑器 — 雷赛步进电机参数与调试面板
========================================

build_leadshine_config_panel
    生成雷赛参数字表单，绑定 system.yaml 中 leadshine_defaults 或
    steppers.<name>.leadshine 字典，修改后随「保存配置」写入 YAML。

LeadShineDebugPanel
    在线调试：读取当前界面配置连接真实电机，调用 hd_ware_tool 底层 API。
    需 hardware.mode == leadshine，且串口可访问。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from config_editor_style import make_button, section_title
from config_editor_widgets import FieldGrid, number_widget, spin_value
from config_labels_zh import (
    LEADSHINE_BOOL_FIELDS,
    LEADSHINE_HOME_FIELDS,
    LEADSHINE_MOTOR_MODE_LABELS,
    LEADSHINE_PR_FIELDS,
    LEADSHINE_SCALAR_FIELDS,
    STEPPER_LABELS,
    leadshine_field_label,
)


def _set_nested(target: dict, key: str, value: Any, on_dirty: Callable[[], None]) -> None:
    target[key] = value
    on_dirty()


def build_leadshine_config_panel(
    data: dict[str, Any],
    on_dirty: Callable[[], None],
    columns: int = 4,
) -> QWidget:
    """
    雷赛参数表单。

    :param data: leadshine_defaults 或 steppers.*.leadshine 配置节
    :param on_dirty: 字段变更时标记配置未保存
    """
    wrap = QWidget()
    layout = QVBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    grid = FieldGrid(columns)

    # 电机控制模式：闭环/开环
    mode = QComboBox()
    for val, zh in LEADSHINE_MOTOR_MODE_LABELS.items():
        mode.addItem(zh, val)
    current = str(data.get("mode", "CLOSE_LOOP"))
    mode.setCurrentIndex(max(mode.findData(current), 0))
    mode.currentIndexChanged.connect(
        lambda _: _set_nested(data, "mode", mode.currentData(), on_dirty)
    )
    grid.add_field(leadshine_field_label("mode"), mode)

    int_fields = {
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
    }
    float_fields = {"pulse_to_distance_ratio"}

    for key in LEADSHINE_SCALAR_FIELDS:
        if key == "mode":
            continue
        if key in float_fields:
            if key not in data:
                continue
            spin = number_widget(data.get(key, 0), False)
        elif key in int_fields:
            spin = number_widget(data.get(key, 0), True)
        else:
            continue
        spin.valueChanged.connect(
            lambda _v, k=key, s=spin: _set_nested(data, k, spin_value(s), on_dirty)
        )
        grid.add_field(leadshine_field_label(key), spin)

    for key in LEADSHINE_BOOL_FIELDS:
        if key not in data:
            data[key] = False
        grid.add_checkbox_field(
            leadshine_field_label(key),
            "启用",
            bool(data.get(key, False)),
            lambda v, k=key: _set_nested(data, k, v, on_dirty),
        )

    layout.addWidget(grid)

    home = data.setdefault("home_parameter", {})
    layout.addWidget(section_title("回零参数"))
    home_grid = FieldGrid(columns)
    for key in LEADSHINE_HOME_FIELDS:
        spin = number_widget(home.get(key, 0), True)
        spin.valueChanged.connect(
            lambda _v, k=key, s=spin: _set_nested(home, k, spin_value(s), on_dirty)
        )
        home_grid.add_field(leadshine_field_label(key), spin)
    layout.addWidget(home_grid)

    pr = data.setdefault("pr_parameter", {})
    layout.addWidget(section_title("PR 参数"))
    pr_grid = FieldGrid(columns)
    for key in LEADSHINE_PR_FIELDS:
        spin = number_widget(pr.get(key, 0), True)
        spin.valueChanged.connect(
            lambda _v, k=key, s=spin: _set_nested(pr, k, spin_value(s), on_dirty)
        )
        pr_grid.add_field(leadshine_field_label(key), spin)
    layout.addWidget(pr_grid)

    layout.addStretch()
    return wrap


class LeadShineDebugPanel(QWidget):
    """
    雷赛步进在线调试面板。

    按钮与 hd_ware_tool.leadshine_motor_ctl.LeadShineMotorControl 方法一一对应。
    连接参数来自内存中的配置（需先保存 YAML 或修改后直接使用当前值）。
    """

    def __init__(self, get_hw_data: Callable[[], dict[str, Any]], parent=None):
        super().__init__(parent)
        self._get_hw_data = get_hw_data
        self._motor = None
        self._connected_key = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(QLabel("选择电机"))
        self._selector = QComboBox()
        self._selector.currentIndexChanged.connect(self._on_motor_changed)
        row.addWidget(self._selector, 1)
        root.addLayout(row)

        btn_row = QHBoxLayout()
        self._btn_connect = make_button("连接", "accent")
        self._btn_enable = make_button("使能", "ghost")
        self._btn_disable = make_button("失能", "ghost")
        self._btn_home = make_button("回零", "ghost")
        self._btn_stop = make_button("停止", "danger")
        self._btn_clear = make_button("清除报警", "ghost")
        self._btn_save = make_button("保存参数", "primary")
        self._btn_refresh = make_button("刷新状态", "ghost")
        for btn in (
            self._btn_connect,
            self._btn_enable,
            self._btn_disable,
            self._btn_home,
            self._btn_stop,
            self._btn_clear,
            self._btn_save,
            self._btn_refresh,
        ):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._status = QLabel("未连接")
        self._status.setObjectName("detailCaption")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        self._btn_connect.clicked.connect(self._toggle_connect)
        self._btn_enable.clicked.connect(lambda: self._run(lambda m: m.enable_motor(True)))
        self._btn_disable.clicked.connect(lambda: self._run(lambda m: m.enable_motor(False)))
        self._btn_home.clicked.connect(lambda: self._run(lambda m: m.return_home()))
        self._btn_stop.clicked.connect(lambda: self._run(lambda m: m.stop_motor()))
        self._btn_clear.clicked.connect(lambda: self._run(lambda m: m.reset_current_warning()))
        self._btn_save.clicked.connect(lambda: self._run(lambda m: m.save_parameters()))
        self._btn_refresh.clicked.connect(self._refresh_status)

        self.reload_motor_list()

    def reload_motor_list(self) -> None:
        hw = self._get_hw_data()
        steppers = hw.get("steppers", {})
        current = self._selector.currentData()
        self._selector.blockSignals(True)
        self._selector.clear()
        for key in steppers:
            self._selector.addItem(STEPPER_LABELS.get(key, key), key)
        if current:
            idx = self._selector.findData(current)
            if idx >= 0:
                self._selector.setCurrentIndex(idx)
        self._selector.blockSignals(False)

    def _on_motor_changed(self) -> None:
        if self._motor:
            self._disconnect()

    def _selected_key(self) -> str:
        return str(self._selector.currentData() or "")

    def _toggle_connect(self) -> None:
        if self._motor:
            self._disconnect()
        else:
            self._connect()

    def _connect(self) -> None:
        key = self._selected_key()
        if not key:
            return
        hw = self._get_hw_data()
        if hw.get("mode") != "leadshine":
            QMessageBox.warning(self, "提示", "请先将硬件模式设为「雷赛 Modbus 步进」")
            return
        try:
            from insert_boom.hardware.leadshine_devices import LeadShineStepperMotor

            cfg = hw.get("steppers", {}).get(key, {})
            defaults = dict(hw.get("leadshine_defaults", {}))
            ls = dict(defaults)
            ls.update(cfg.get("leadshine", {}))
            ls.setdefault("slave_id", cfg.get("slave_id", cfg.get("id", 1)))
            serial = hw.get("serial_defaults", {})
            baud = int(cfg.get("baudrate", serial.get("baudrate", 115200)))
            delay = float(ls.get("delay_read_write", serial.get("delay_read_write", 0.05)))

            motor = LeadShineStepperMotor(
                name=key,
                motor_id=int(cfg.get("id", 1)),
                port=str(cfg.get("port", "")),
                baudrate=baud,
                home_position=int(cfg.get("home_position", 0)),
                motion_timeout=float(cfg.get("motion_timeout", serial.get("motion_timeout", 30))),
                delay_read_write=delay,
                leadshine_cfg=ls,
            )
            if not motor.connect():
                QMessageBox.critical(self, "连接失败", f"无法连接 {STEPPER_LABELS.get(key, key)}")
                return
            self._motor = motor
            self._connected_key = key
            self._btn_connect.setText("断开")
            self._refresh_status()
        except Exception as exc:
            QMessageBox.critical(self, "连接失败", str(exc))

    def _disconnect(self) -> None:
        if self._motor:
            try:
                self._motor.disconnect()
            except Exception:
                pass
        self._motor = None
        self._connected_key = ""
        self._btn_connect.setText("连接")
        self._status.setText("未连接")

    def _raw(self):
        if not self._motor:
            QMessageBox.information(self, "提示", "请先连接电机")
            return None
        raw = self._motor.get_raw_motor()
        if raw is None:
            QMessageBox.warning(self, "提示", "电机未就绪")
            return None
        return raw

    def _run(self, fn) -> None:
        raw = self._raw()
        if raw is None:
            return
        try:
            fn(raw)
            self._refresh_status()
        except Exception as exc:
            QMessageBox.critical(self, "操作失败", str(exc))

    def _refresh_status(self) -> None:
        if not self._motor:
            self._status.setText("未连接")
            return
        try:
            pos = self._motor.get_position()
            vel = self._motor.get_velocity()
            text = self._motor.get_status_text()
            self._status.setText(
                f"电机: {STEPPER_LABELS.get(self._connected_key, self._connected_key)}\n"
                f"位置: {pos} pulse   速度: {vel} rpm\n"
                f"状态: {text}"
            )
        except Exception as exc:
            self._status.setText(f"读取状态失败: {exc}")

    def closeEvent(self, event) -> None:
        self._disconnect()
        super().closeEvent(event)
