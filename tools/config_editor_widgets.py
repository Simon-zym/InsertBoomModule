"""配置编辑器 — 统一布局组件"""

from __future__ import annotations

from typing import Any, Callable, Optional, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config_editor_style import form_label, make_card, make_toolbar_strip

PAGE_MARGIN = (12, 8, 12, 8)
GRID_H_SPACING = 10
GRID_V_SPACING = 8
NAV_WIDTH = 220
INPUT_HEIGHT = 30
FORM_MAX_WIDTH = 820


def _scroll(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(inner)
    return area


def _uniform(widget: QWidget) -> QWidget:
    widget.setFixedHeight(INPUT_HEIGHT)
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return widget


class FieldGrid(QWidget):
    """紧凑多列表单网格"""

    def __init__(self, columns: int = 4, parent=None):
        super().__init__(parent)
        self._columns = max(1, columns)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(GRID_H_SPACING)
        self._grid.setVerticalSpacing(GRID_V_SPACING)
        self._index = 0
        self.setMaximumWidth(FORM_MAX_WIDTH)

    def add_field(self, label: str, widget: QWidget) -> QWidget:
        row = self._index // self._columns
        col = self._index % self._columns
        cell = QFrame()
        cell.setObjectName("fieldCell")
        lay = QVBoxLayout(cell)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(5)
        lay.addWidget(form_label(label))
        lay.addWidget(_uniform(widget))
        self._grid.addWidget(cell, row, col)
        self._index += 1
        return widget

    def add_checkbox_field(self, label: str, text: str, checked: bool, on_change) -> QCheckBox:
        chk = QCheckBox(text)
        chk.setChecked(checked)
        chk.setMinimumHeight(INPUT_HEIGHT)
        chk.stateChanged.connect(lambda s: on_change(s == Qt.Checked))
        self.add_field(label, chk)
        return chk


class TableCellCombo(QWidget):
    """表格单元格内紧凑下拉框"""

    def __init__(
        self,
        items: list[tuple[str, str]],
        current: str,
        on_change: Callable[[str], None],
        parent=None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(0)
        self.combo = QComboBox()
        self.combo.setObjectName("tableCombo")
        for val, text in items:
            self.combo.addItem(text, val)
        idx = self.combo.findData(current)
        self.combo.setCurrentIndex(max(idx, 0))
        self.combo.currentIndexChanged.connect(
            lambda _: on_change(self.combo.currentData())
        )
        layout.addWidget(self.combo)
        self.setFixedHeight(32)


class NavMasterDetail(QWidget):
    """左侧导航 + 右侧紧凑编辑区"""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = make_card()
        root = QHBoxLayout(outer)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        nav_box = QFrame()
        nav_box.setObjectName("navBox")
        nav_outer = QVBoxLayout(nav_box)
        nav_outer.setContentsMargins(8, 8, 8, 8)
        nav_outer.setSpacing(6)
        self._nav_title = QLabel("配置项")
        self._nav_title.setObjectName("panelTitle")
        nav_outer.addWidget(self._nav_title)

        from PyQt5.QtWidgets import QListWidget

        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        nav_outer.addWidget(self.nav, 1)
        nav_box.setFixedWidth(NAV_WIDTH)
        root.addWidget(nav_box)

        self.stack = QStackedWidget()
        self.stack.setObjectName("detailStack")
        root.addWidget(self.stack, 1)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.addWidget(outer)

        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self._page_titles: list[str] = []

    def set_nav_title(self, text: str) -> None:
        self._nav_title.setText(text)

    def add_page(self, title: str, widget: QWidget, scroll: bool = False) -> None:
        from PyQt5.QtWidgets import QListWidgetItem

        self._page_titles.append(title)
        self.nav.addItem(QListWidgetItem(title))

        panel = QFrame()
        panel.setObjectName("detailPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 10, 14, 10)
        panel_layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("detailTitle")
        panel_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        content = _scroll(widget) if scroll else widget
        body_layout.addWidget(content, 0, Qt.AlignTop | Qt.AlignLeft)
        body_layout.addStretch(1)
        panel_layout.addWidget(body, 1)

        page_wrapper = QWidget()
        wrap_layout = QVBoxLayout(page_wrapper)
        wrap_layout.setContentsMargins(*PAGE_MARGIN)
        wrap_layout.setSpacing(0)
        wrap_layout.addWidget(panel, 1)
        self.stack.addWidget(page_wrapper)

    def _on_nav_changed(self, row: int) -> None:
        if row >= 0:
            self.stack.setCurrentIndex(row)

    def select(self, row: int = 0) -> None:
        if self.nav.count():
            self.nav.setCurrentRow(row)


def number_widget(value: Any, as_int: bool) -> QWidget:
    if as_int:
        spin = QSpinBox()
        spin.setRange(-999999999, 999999999)
        spin.setValue(int(value or 0))
        return spin
    spin = QDoubleSpinBox()
    spin.setRange(-999999.0, 999999.0)
    spin.setDecimals(4)
    spin.setValue(float(value or 0))
    return spin


def spin_value(spin: QWidget) -> Any:
    if isinstance(spin, QSpinBox):
        return int(spin.value())
    return float(spin.value())


def build_field_grid(
    data: dict,
    fields: list[str],
    on_dirty: Callable[[], None],
    columns: int = 4,
    text_fields: Optional[Set[str]] = None,
    int_fields: Optional[Set[str]] = None,
) -> FieldGrid:
    from config_labels_zh import field_label

    text_fields = text_fields or set()
    int_fields = int_fields or {"id", "baudrate", "max_speed", "slave_id"}
    grid = FieldGrid(columns)

    def _set(key: str, value: Any) -> None:
        data[key] = value
        on_dirty()

    for key in fields:
        value = data.get(key)
        label = field_label(key)
        if key in text_fields or key in ("port", "config_file", "ready_sensor"):
            edit = QLineEdit(str(value if value is not None else ""))
            edit.textChanged.connect(lambda t, k=key: _set(k, t))
            grid.add_field(label, edit)
        elif isinstance(value, bool):
            grid.add_checkbox_field(label, "启用", bool(value), lambda v, k=key: _set(k, v))
        elif isinstance(value, int) or key in int_fields:
            spin = number_widget(value, True)
            spin.valueChanged.connect(lambda _v, k=key, s=spin: _set(k, spin_value(s)))
            grid.add_field(label, spin)
        elif isinstance(value, float):
            spin = number_widget(value, False)
            spin.valueChanged.connect(lambda _v, k=key, s=spin: _set(k, spin_value(s)))
            grid.add_field(label, spin)
        else:
            edit = QLineEdit(str(value if value is not None else ""))
            edit.textChanged.connect(lambda t, k=key: _set(k, t))
            grid.add_field(label, edit)
    return grid


def build_dynamic_grid(
    data: dict,
    on_dirty: Callable[[], None],
    columns: int = 4,
) -> FieldGrid:
    from config_labels_zh import field_label

    grid = FieldGrid(columns)

    def _set(key: str, value: Any) -> None:
        data[key] = value
        on_dirty()

    for key, value in data.items():
        label = field_label(key)
        if isinstance(value, bool):
            grid.add_checkbox_field(label, "启用", value, lambda v, k=key: _set(k, v))
        elif isinstance(value, int):
            spin = number_widget(value, True)
            spin.valueChanged.connect(lambda _v, k=key, s=spin: _set(k, spin_value(s)))
            grid.add_field(label, spin)
        elif isinstance(value, float):
            spin = number_widget(value, False)
            spin.valueChanged.connect(lambda _v, k=key, s=spin: _set(k, spin_value(s)))
            grid.add_field(label, spin)
        else:
            edit = QLineEdit(str(value))
            edit.textChanged.connect(lambda t, k=key: _set(k, t))
            grid.add_field(label, edit)
    return grid


def toolbar(*buttons: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(10, 8, 10, 8)
    row.setSpacing(8)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


def wrap_toolbar(*buttons: QWidget) -> QFrame:
    """带背景的工具栏条"""
    strip = make_toolbar_strip()
    lay = toolbar(*buttons)
    strip.setLayout(lay)
    return strip


def question_yes_no(parent: QWidget, title: str, text: str, default_yes: bool = False) -> bool:
    """是 / 否 确认框"""
    box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, parent)
    yes_btn = box.addButton("是", QMessageBox.YesRole)
    no_btn = box.addButton("否", QMessageBox.NoRole)
    box.setDefaultButton(yes_btn if default_yes else no_btn)
    box.exec_()
    return box.clickedButton() == yes_btn


def question_ok_cancel(parent: QWidget, title: str, text: str, default_ok: bool = False) -> bool:
    """确定 / 取消 确认框"""
    box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, parent)
    ok_btn = box.addButton("确定", QMessageBox.AcceptRole)
    cancel_btn = box.addButton("取消", QMessageBox.RejectRole)
    box.setDefaultButton(ok_btn if default_ok else cancel_btn)
    box.exec_()
    return box.clickedButton() == ok_btn


def question_save_discard_cancel(parent: QWidget, title: str, text: str) -> int:
    """保存 / 不保存 / 取消 三选一"""
    box = QMessageBox(QMessageBox.Question, title, text, QMessageBox.NoButton, parent)
    save_btn = box.addButton("保存", QMessageBox.AcceptRole)
    discard_btn = box.addButton("不保存", QMessageBox.DestructiveRole)
    cancel_btn = box.addButton("取消", QMessageBox.RejectRole)
    box.setDefaultButton(save_btn)
    box.exec_()
    clicked = box.clickedButton()
    if clicked == save_btn:
        return QMessageBox.Save
    if clicked == discard_btn:
        return QMessageBox.Discard
    return QMessageBox.Cancel
