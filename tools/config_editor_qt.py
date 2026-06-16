#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InsertBoom 配置文件编辑器 (PyQt5)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Optional

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config_editor_leadshine import LeadShineDebugPanel, build_leadshine_config_panel
from config_editor_style import apply_theme, header_bar, make_button, make_card, section_title
from config_editor_widgets import (
    FieldGrid,
    NavMasterDetail,
    TableCellCombo,
    build_dynamic_grid,
    build_field_grid,
    number_widget,
    question_ok_cancel,
    question_save_discard_cancel,
    question_yes_no,
    spin_value,
    wrap_toolbar,
)
from config_labels_zh import (
    GRIPPER_ACTIONS,
    HW_MODE_LABELS,
    WAYPOINT_TABLE_HEADERS,
    field_label,
    group_label,
    waypoint_config_name,
    waypoint_display_name,
)
from config_store import CONFIG_FILES, PROJECT_ROOT, load_config, save_config

# 途径点表格列宽 / 行高
WP_COL_WIDTHS = [140, 72, 72, 72, 72, 72, 72, 52, 112, 52]
WP_ROW_HEIGHT = 38
WP_NAME_ROLE = Qt.UserRole


class ConfigPageBase(QWidget):
    def __init__(self, config_id: str, on_dirty: Callable[[], None], parent=None):
        super().__init__(parent)
        self.config_id = config_id
        self.on_dirty = on_dirty
        self.data: dict[str, Any] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)

    def mark_dirty(self) -> None:
        self.on_dirty()

    def load_data(self, data: dict[str, Any]) -> None:
        self.data = data
        self.rebuild()

    def collect_data(self) -> dict[str, Any]:
        return self.data

    def clear_body(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def rebuild(self) -> None:
        raise NotImplementedError

    @staticmethod
    def _set(target: dict, key: str, value: Any) -> None:
        target[key] = value


class SystemConfigPage(ConfigPageBase):
    """系统硬件配置页 — 含雷赛步进全局/调试及各电机参数"""

    def rebuild(self) -> None:
        self.clear_body()
        hw = self.data.setdefault("hardware", {})
        robots = self.data.setdefault("robots", {})

        nav = NavMasterDetail()
        nav.set_nav_title("硬件分类")

        # 基本设置
        basic = FieldGrid(4)
        mode = QComboBox()
        for val, zh in HW_MODE_LABELS.items():
            mode.addItem(zh, val)
        mode.setCurrentIndex(max(mode.findData(hw.get("mode", "mock")), 0))
        mode.currentIndexChanged.connect(
            lambda _: self._set(hw, "mode", mode.currentData()) or self.mark_dirty()
        )
        basic.add_field(field_label("mode"), mode)
        serial = hw.setdefault("serial_defaults", {})
        for key in ("baudrate", "timeout", "motion_timeout", "delay_read_write"):
            spin = number_widget(serial.get(key), key in ("baudrate",))
            spin.valueChanged.connect(
                lambda _v, k=key, s=spin: self._set(serial, k, spin_value(s)) or self.mark_dirty()
            )
            basic.add_field(field_label(key), spin)
        nav.add_page("基本设置", basic)

        # 雷赛 Modbus 全局默认 → config/system.yaml → hardware.leadshine_defaults
        ls_defaults = hw.setdefault("leadshine_defaults", {})
        ls_panel = build_leadshine_config_panel(ls_defaults, self.mark_dirty, columns=4)
        nav.add_page("雷赛步进 (全局)", ls_panel)

        # 在线调试：连接串口并调用 enable/home/stop 等接口
        nav.add_page(
            "雷赛步进 (调试)",
            LeadShineDebugPanel(lambda: self.data.setdefault("hardware", {})),
        )

        for key, cfg in hw.setdefault("steppers", {}).items():
            page = QWidget()
            page_lay = QVBoxLayout(page)
            page_lay.setContentsMargins(0, 0, 0, 0)
            page_lay.setSpacing(10)
            page_lay.addWidget(section_title("串口与运动参数"))
            fields = ["id", "slave_id", "port", "home_position", "pulses_per_ms", "max_speed"]
            fields += [f for f in ("press_position", "insert_position", "tighten_steps") if f in cfg]
            grid = build_field_grid(
                cfg, fields, self.mark_dirty, columns=4,
                text_fields={"port"},
                float_fields={"pulses_per_ms"},
            )
            page_lay.addWidget(grid)
            # 单电机雷赛覆盖项 → steppers.<name>.leadshine
            ls_cfg = cfg.setdefault("leadshine", {})
            page_lay.addWidget(section_title("雷赛参数 (可覆盖全局)"))
            page_lay.addWidget(build_leadshine_config_panel(ls_cfg, self.mark_dirty, columns=4))
            page_lay.addStretch()
            nav.add_page(group_label("stepper", key), page)

        for key, cfg in hw.setdefault("cylinders", {}).items():
            grid = build_field_grid(
                cfg, ["port", "extend_timeout", "retract_timeout"],
                self.mark_dirty, columns=4, text_fields={"port"},
            )
            nav.add_page(group_label("cylinder", key), grid)

        for key, cfg in hw.setdefault("sensors", {}).items():
            grid = FieldGrid(2)
            grid.add_checkbox_field(
                field_label("initial_value"),
                "已触发 / 已遮挡",
                bool(cfg.get("initial_value", False)),
                lambda v: self._set(cfg, "initial_value", v) or self.mark_dirty(),
            )
            nav.add_page(group_label("sensor", key), grid)

        for key, cfg in hw.setdefault("grippers", {}).items():
            grid = build_field_grid(cfg, list(cfg.keys()), self.mark_dirty, columns=4)
            nav.add_page(group_label("gripper", key), grid)

        for key, cfg in robots.items():
            grid = build_field_grid(
                cfg, ["ip", "port", "config_file"],
                self.mark_dirty, columns=4, text_fields={"ip", "config_file"},
            )
            nav.add_page(group_label("robot", key), grid)

        nav.select(0)
        self._layout.addWidget(nav, 1)


class WorkflowConfigPage(ConfigPageBase):
    def rebuild(self) -> None:
        self.clear_body()
        wf = self.data.setdefault("workflow", {})
        nav = NavMasterDetail()
        nav.set_nav_title("流程步骤")

        global_grid = FieldGrid(4)
        name_edit = QLineEdit(str(wf.get("name", "")))
        name_edit.textChanged.connect(lambda t: self._set(wf, "name", t) or self.mark_dirty())
        global_grid.add_field("流程名称", name_edit)

        for key, as_int in [("max_retries", True), ("retry_delay_sec", False), ("step_timeout", False)]:
            spin = QSpinBox() if as_int else QDoubleSpinBox()
            if as_int:
                spin.setRange(0, 9999)
                spin.setValue(int(wf.get(key, 0)))
                spin.valueChanged.connect(lambda v, k=key: self._set(wf, k, int(v)) or self.mark_dirty())
            else:
                spin.setRange(0, 99999)
                spin.setDecimals(2)
                spin.setValue(float(wf.get(key, 0)))
                spin.valueChanged.connect(lambda v, k=key: self._set(wf, k, float(v)) or self.mark_dirty())
            global_grid.add_field(field_label(key), spin)

        global_grid.add_checkbox_field(
            field_label("auto_rollback"),
            "失败后自动回滚",
            bool(wf.get("auto_rollback", False)),
            lambda v: self._set(wf, "auto_rollback", v) or self.mark_dirty(),
        )
        nav.add_page("全局参数", global_grid)

        for step_key, params in wf.setdefault("steps", {}).items():
            nav.add_page(group_label("step", step_key), build_dynamic_grid(params, self.mark_dirty, columns=4))

        nav.select(0)
        self._layout.addWidget(nav, 1)


class WaypointsConfigPage(ConfigPageBase):
    COL_HEADERS = WAYPOINT_TABLE_HEADERS

    def __init__(self, config_id: str, on_dirty: Callable[[], None], parent=None):
        super().__init__(config_id, on_dirty, parent)
        self._current_key: Optional[str] = None
        self._list = None
        self._right: Optional[QFrame] = None
        self._right_outer: Optional[QVBoxLayout] = None
        self._content: Optional[QWidget] = None
        self._right_layout: Optional[QVBoxLayout] = None
        self._table: Optional[QTableWidget] = None
        self._table_connected = False

    def rebuild(self) -> None:
        self.clear_body()
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = make_card()
        left.setFixedWidth(220)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)
        left_layout.addWidget(section_title("流程列表", "选择流程或命名位姿"))

        from PyQt5.QtWidgets import QListWidget, QListWidgetItem

        self._list = QListWidget()
        self._list.setObjectName("navList")
        self._list.currentRowChanged.connect(self._on_select)
        for key in self.data:
            item = QListWidgetItem(group_label("process", key))
            item.setData(Qt.UserRole, key)
            self._list.addItem(item)
        left_layout.addWidget(self._list, 1)
        splitter.addWidget(left)

        self._right = make_card()
        self._right_outer = QVBoxLayout(self._right)
        self._right_outer.setContentsMargins(14, 12, 14, 12)
        self._right_outer.setSpacing(10)
        self._reset_content()
        self._show_empty_hint()
        splitter.addWidget(self._right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self._layout.addWidget(splitter, 1)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _show_empty_hint(self) -> None:
        hint = QLabel("← 请从左侧选择流程")
        hint.setObjectName("sectionHint")
        hint.setAlignment(Qt.AlignCenter)
        self._right_layout.addStretch(1)
        self._right_layout.addWidget(hint)
        self._right_layout.addStretch(1)

    def _reset_content(self) -> None:
        """销毁并重建右侧内容区，避免切换流程时残留控件"""
        if self._content is not None:
            self._content.hide()
            if self._right_outer is not None:
                self._right_outer.removeWidget(self._content)
            self._content.setParent(None)
            self._content.deleteLater()
            self._content = None
        self._content = QWidget()
        self._right_layout = QVBoxLayout(self._content)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(10)
        if self._right_outer is not None:
            self._right_outer.addWidget(self._content, 1)
        self._table = None
        self._table_connected = False

    def _clear_right(self) -> None:
        self._reset_content()

    def _on_select(self, row: int) -> None:
        self._clear_right()
        if row < 0:
            self._show_empty_hint()
            return

        key = self._list.item(row).data(Qt.UserRole)
        self._current_key = key
        value = self.data.get(key)
        if not isinstance(value, dict):
            return

        title = QLabel(group_label("process", key))
        title.setObjectName("sectionTitle")
        self._right_layout.addWidget(title)

        if "waypoints" in value:
            self._build_process_editor(value)
        elif "position" in value:
            self._build_pose_editor(value)
            self._right_layout.addStretch(1)

    def _build_pose_editor(self, pose: dict) -> None:
        pos = pose.setdefault("position", {"x": 0, "y": 0, "z": 0})
        euler = pose.setdefault("euler", {"roll": 0, "pitch": 0, "yaw": 0})
        grid = FieldGrid(4)

        for coord, box in [("x", pos), ("y", pos), ("z", pos)]:
            spin = QDoubleSpinBox()
            spin.setRange(-10, 10)
            spin.setDecimals(4)
            spin.setValue(float(box.get(coord, 0)))
            spin.valueChanged.connect(lambda v, c=coord, d=box: self._set(d, c, float(v)) or self.mark_dirty())
            grid.add_field(field_label(coord), spin)

        for coord, box in [("roll", euler), ("pitch", euler), ("yaw", euler)]:
            spin = QDoubleSpinBox()
            spin.setRange(-6.28, 6.28)
            spin.setDecimals(4)
            spin.setValue(float(box.get(coord, 0)))
            spin.valueChanged.connect(lambda v, c=coord, d=box: self._set(d, c, float(v)) or self.mark_dirty())
            grid.add_field(field_label(coord), spin)

        speed = QSpinBox()
        speed.setRange(1, 100)
        speed.setValue(int(pose.get("speed", 20)))
        speed.valueChanged.connect(lambda v: self._set(pose, "speed", int(v)) or self.mark_dirty())
        grid.add_field(field_label("speed"), speed)

        self._right_layout.addWidget(grid)

    def _build_process_editor(self, process: dict) -> None:
        meta = FieldGrid(2)
        meta.setMaximumWidth(680)
        name_edit = QLineEdit(str(process.get("name", "")))
        name_edit.textChanged.connect(lambda t: self._set(process, "name", t) or self.mark_dirty())
        meta.add_field(field_label("internal_name"), name_edit)
        desc_edit = QLineEdit(str(process.get("description", "")))
        desc_edit.textChanged.connect(lambda t: self._set(process, "description", t) or self.mark_dirty())
        meta.add_field(field_label("description"), desc_edit)
        self._right_layout.addWidget(meta)

        add_btn = make_button("＋ 末尾添加", "ghost")
        insert_btn = make_button("⊕ 插入", "accent")
        del_btn = make_button("删除选中", "danger")
        up_btn = make_button("↑ 上移")
        down_btn = make_button("↓ 下移")
        add_btn.clicked.connect(lambda: self._add_waypoint(process))
        insert_btn.clicked.connect(lambda: self._insert_waypoint(process))
        del_btn.clicked.connect(lambda: self._delete_waypoints(process))
        up_btn.clicked.connect(lambda: self._move_waypoint(process, -1))
        down_btn.clicked.connect(lambda: self._move_waypoint(process, 1))
        self._right_layout.addWidget(wrap_toolbar(add_btn, insert_btn, del_btn, up_btn, down_btn))

        self._table = QTableWidget()
        self._table.setObjectName("waypointTable")
        self._table.setColumnCount(len(self.COL_HEADERS))
        self._table.setHorizontalHeaderLabels(self.COL_HEADERS)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.ExtendedSelection)
        self._table.verticalHeader().setDefaultSectionSize(WP_ROW_HEIGHT)
        self._table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        header = self._table.horizontalHeader()
        for i, w in enumerate(WP_COL_WIDTHS):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self._table.setColumnWidth(i, w)
        header.setStretchLastSection(False)
        self._table.setMinimumWidth(sum(WP_COL_WIDTHS) + 24)

        self._fill_table(process)

        table_scroll = QScrollArea()
        table_scroll.setObjectName("waypointTableScroll")
        table_scroll.setWidgetResizable(True)
        table_scroll.setFrameShape(QFrame.NoFrame)
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll.setWidget(self._table)
        self._right_layout.addWidget(table_scroll, 1)

    def _fill_table(self, process: dict) -> None:
        waypoints = process.setdefault("waypoints", [])
        self._table.blockSignals(True)
        self._table.setRowCount(len(waypoints))

        for row, wp in enumerate(waypoints):
            pos = wp.setdefault("position", {"x": 0, "y": 0, "z": 0})
            euler = wp.setdefault("euler", {"roll": 0, "pitch": 0, "yaw": 0})
            raw_name = str(wp.get("name", ""))
            zh_name = waypoint_display_name(raw_name)
            name_item = QTableWidgetItem(zh_name)
            name_item.setData(WP_NAME_ROLE, raw_name)
            name_item.setToolTip(f"配置标识: {raw_name}" if raw_name != zh_name else "")
            self._table.setItem(row, 0, name_item)
            for col, val in enumerate(
                [pos["x"], pos["y"], pos["z"], euler["roll"], euler["pitch"], euler["yaw"], wp.get("speed", 15)],
                start=1,
            ):
                self._table.setItem(row, col, QTableWidgetItem(f"{val:g}" if isinstance(val, float) else str(val)))

            combo_wrap = TableCellCombo(
                GRIPPER_ACTIONS,
                wp.get("gripper_action", "none") or "none",
                lambda val, r=row, p=process: self._on_gripper_changed(r, val, p),
            )
            self._table.setCellWidget(row, 8, combo_wrap)
            self._table.setItem(row, 9, QTableWidgetItem(str(wp.get("trajectory_connect", 0) or 0)))

        self._table.blockSignals(False)
        if not self._table_connected:
            self._table.cellChanged.connect(self._on_cell_changed)
            self._table_connected = True

    def _on_gripper_changed(self, row: int, action: str, process: dict) -> None:
        wps = process.get("waypoints", [])
        if row < len(wps):
            wps[row]["gripper_action"] = action
            self.mark_dirty()

    def _on_cell_changed(self, row: int, col: int) -> None:
        if not self._current_key or col == 8:
            return
        wps = self.data.get(self._current_key, {}).get("waypoints", [])
        if row >= len(wps):
            return
        wp, pos, euler = wps[row], wps[row].setdefault("position", {}), wps[row].setdefault("euler", {})
        item = self._table.item(row, col)
        text = item.text() if item else ""
        try:
            if col == 0:
                config_name = waypoint_config_name(text)
                wp["name"] = config_name
                item.setData(WP_NAME_ROLE, config_name)
                item.setText(waypoint_display_name(config_name))
                item.setToolTip(
                    f"配置标识: {config_name}" if config_name != item.text() else ""
                )
            elif col == 1:
                pos["x"] = float(text)
            elif col == 2:
                pos["y"] = float(text)
            elif col == 3:
                pos["z"] = float(text)
            elif col == 4:
                euler["roll"] = float(text)
            elif col == 5:
                euler["pitch"] = float(text)
            elif col == 6:
                euler["yaw"] = float(text)
            elif col == 7:
                wp["speed"] = int(float(text))
            elif col == 9:
                val = int(float(text or 0))
                if val == 0:
                    wp.pop("trajectory_connect", None)
                else:
                    wp["trajectory_connect"] = val
            else:
                return
            self.mark_dirty()
        except ValueError:
            return

    @staticmethod
    def _new_waypoint(process: dict) -> dict:
        wps = process.get("waypoints", [])
        return {
            "name": f"途径点_{len(wps) + 1}",
            "position": {"x": 0, "y": 0, "z": 0},
            "euler": {"roll": 3.141, "pitch": 0, "yaw": 0},
            "speed": 15,
            "gripper_action": "none",
        }

    def _insert_index(self) -> int:
        """在选中行处插入；未选中则插在末尾"""
        if not self._table:
            return 0
        rows = {idx.row() for idx in self._table.selectedIndexes()}
        if not rows:
            return self._table.rowCount()
        return min(rows)

    def _add_waypoint(self, process: dict) -> None:
        wps = process.setdefault("waypoints", [])
        wps.append(self._new_waypoint(process))
        self.mark_dirty()
        self._on_select(self._list.currentRow())
        if self._table:
            self._table.selectRow(len(wps) - 1)

    def _insert_waypoint(self, process: dict) -> None:
        wps = process.setdefault("waypoints", [])
        insert_at = self._insert_index()
        wps.insert(insert_at, self._new_waypoint(process))
        self.mark_dirty()
        self._on_select(self._list.currentRow())
        if self._table:
            self._table.selectRow(insert_at)

    def _delete_waypoints(self, process: dict) -> None:
        if not self._table:
            return
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "提示", "请先在表格中选中要删除的途径点（可多选）")
            return
        wps = process.get("waypoints", [])
        if len(rows) > 1:
            if not question_yes_no(self, "确认删除", f"确定删除选中的 {len(rows)} 个途径点吗？"):
                return
        for row in rows:
            if 0 <= row < len(wps):
                del wps[row]
        self.mark_dirty()
        self._on_select(self._list.currentRow())

    def _move_waypoint(self, process: dict, direction: int) -> None:
        row = self._table.currentRow() if self._table else -1
        wps = process.get("waypoints", [])
        new_row = row + direction
        if 0 <= row < len(wps) and 0 <= new_row < len(wps):
            wps[row], wps[new_row] = wps[new_row], wps[row]
            self.mark_dirty()
            self._on_select(self._list.currentRow())
            self._table.selectRow(new_row)


class ConfigEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InsertBoom 配置编辑器")
        self.resize(1360, 860)
        self.setMinimumSize(1100, 700)
        self._dirty = False
        self._pages: dict[str, ConfigPageBase] = {}
        self._prev_index = 0
        self._building = False

        central = QWidget()
        central.setObjectName("contentArea")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(header_bar(
            "InsertBoom 配置中心", "系统硬件 · 装配流程 · 机械臂途径点",
            self.save_current, self.reload_current,
        ))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 10)
        body_layout.setSpacing(0)
        body.setObjectName("tabBody")
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        body_layout.addWidget(self.tabs, 1)
        root.addWidget(body, 1)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        for cid, meta in CONFIG_FILES.items():
            page = {"system": SystemConfigPage, "workflow": WorkflowConfigPage}.get(cid, WaypointsConfigPage)(cid, self._mark_dirty)
            self._pages[cid] = page
            self.tabs.addTab(page, meta["title"])

        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(0)
        self.tabs.blockSignals(False)
        self._load_tab(0)
        self._update_status()

    def _mark_dirty(self) -> None:
        if not self._building:
            self._dirty = True
            self._update_status()

    def _update_status(self) -> None:
        idx = self.tabs.currentIndex()
        cid = list(CONFIG_FILES.keys())[idx]
        dirty = "  ● 未保存" if self._dirty else ""
        self.statusBar().showMessage(f"项目: {PROJECT_ROOT}  |  文件: {CONFIG_FILES[cid]['path']}{dirty}")
        self.setWindowTitle(f"InsertBoom 配置编辑器 — {CONFIG_FILES[cid]['title']}{dirty}")

    def _on_tab_changed(self, index: int) -> None:
        if index < 0:
            return
        if self._dirty:
            ans = question_save_discard_cancel(
                self, "未保存", "当前有未保存修改，是否保存后再切换？",
            )
            if ans == QMessageBox.Save and not self.save_current():
                self.tabs.blockSignals(True)
                self.tabs.setCurrentIndex(self._prev_index)
                self.tabs.blockSignals(False)
                return
            if ans == QMessageBox.Cancel:
                self.tabs.blockSignals(True)
                self.tabs.setCurrentIndex(self._prev_index)
                self.tabs.blockSignals(False)
                return
        self._prev_index = index
        self._load_tab(index)

    def _load_tab(self, index: int) -> None:
        cid = list(CONFIG_FILES.keys())[index]
        self._building = True
        try:
            self._pages[cid].load_data(load_config(cid))
            self._dirty = False
        finally:
            self._building = False
        self._update_status()

    def reload_current(self) -> None:
        if self._dirty and not question_ok_cancel(self, "确认", "未保存修改将丢失，确定重新加载？"):
            return
        self._load_tab(self.tabs.currentIndex())
        QMessageBox.information(self, "完成", "已从文件重新加载")

    def save_current(self) -> bool:
        cid = list(CONFIG_FILES.keys())[self.tabs.currentIndex()]
        try:
            path = save_config(cid, self._pages[cid].collect_data())
            self._dirty = False
            self._update_status()
            QMessageBox.information(self, "保存成功", f"已保存到:\n{path}")
            return True
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return False

    def closeEvent(self, event) -> None:
        if self._dirty:
            ans = question_save_discard_cancel(self, "退出", "有未保存修改，是否保存后退出？")
            if ans == QMessageBox.Save and not self.save_current():
                event.ignore()
                return
            if ans == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("InsertBoom 配置编辑器")
    apply_theme(app)
    win = ConfigEditorWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
