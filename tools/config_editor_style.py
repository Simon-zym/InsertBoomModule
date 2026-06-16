"""InsertBoom 配置编辑器 — 界面主题与样式工具"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

# 配色 — 工业控制台风格
C_BG = "#eef2f6"
C_BG_SOFT = "#f8fafc"
C_SURFACE = "#ffffff"
C_SURFACE_2 = "#fbfcfd"
C_HEADER = "#0c1222"
C_HEADER_2 = "#151d32"
C_ACCENT = "#2563eb"
C_ACCENT_LIGHT = "#dbeafe"
C_ACCENT_SOFT = "#eff6ff"
C_ACCENT_HOVER = "#1d4ed8"
C_TEXT = "#0f172a"
C_TEXT_SEC = "#334155"
C_TEXT_MUTED = "#64748b"
C_BORDER = "#e2e8f0"
C_BORDER_LIGHT = "#f1f5f9"
C_SUCCESS = "#059669"
C_DANGER = "#dc2626"
C_DANGER_BG = "#fef2f2"
C_SHADOW = "rgba(15, 23, 42, 0.06)"

APP_STYLESHEET = f"""
* {{
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {C_TEXT};
    outline: none;
}}

QMainWindow {{
    background: {C_BG};
}}

QWidget#tabBody {{
    background: transparent;
}}

QWidget#contentArea {{
    background: {C_BG};
}}

/* ---------- 顶栏 ---------- */
QFrame#headerBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {C_HEADER}, stop:1 {C_HEADER_2});
    border: none;
    border-bottom: 2px solid {C_ACCENT};
}}

QLabel#brandTitle {{
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: transparent;
}}

QLabel#brandSubtitle {{
    color: #94a3b8;
    font-size: 11px;
    background: transparent;
}}

QPushButton#headerGhostBtn {{
    background: rgba(255, 255, 255, 0.08);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    min-height: 32px;
}}

QPushButton#headerGhostBtn:hover {{
    background: rgba(255, 255, 255, 0.14);
    color: #ffffff;
    border-color: rgba(255, 255, 255, 0.28);
}}

QPushButton#headerPrimaryBtn {{
    background: {C_ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 600;
    min-height: 32px;
}}

QPushButton#headerPrimaryBtn:hover {{
    background: {C_ACCENT_HOVER};
}}

/* ---------- 主标签页 ---------- */
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    border-radius: 14px;
    background: {C_SURFACE};
    top: -1px;
}}

QTabWidget#mainTabs::pane {{
    padding: 4px;
    background: {C_SURFACE};
}}

QTabWidget#mainTabs > QTabBar::tab {{
    background: transparent;
    color: {C_TEXT_MUTED};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 22px;
    margin: 0 2px;
    font-size: 13px;
    font-weight: 500;
    min-width: 96px;
}}

QTabWidget#mainTabs > QTabBar::tab:selected {{
    color: {C_ACCENT};
    border-bottom: 2px solid {C_ACCENT};
    font-weight: 600;
}}

QTabWidget#mainTabs > QTabBar::tab:hover:!selected {{
    color: {C_TEXT_SEC};
    background: {C_ACCENT_SOFT};
    border-radius: 8px 8px 0 0;
}}

/* ---------- 卡片 / 面板 ---------- */
QFrame#card {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 14px;
}}

QFrame#navBox {{
    background: {C_BG_SOFT};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
}}

QFrame#detailPanel {{
    background: {C_SURFACE_2};
    border: 1px solid {C_BORDER_LIGHT};
    border-radius: 12px;
}}

QFrame#toolBarStrip {{
    background: {C_BG_SOFT};
    border: 1px solid {C_BORDER_LIGHT};
    border-radius: 10px;
}}

QFrame#sidePanel {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 14px;
}}

/* ---------- 标题文字 ---------- */
QLabel#sectionTitle {{
    color: {C_TEXT};
    font-size: 15px;
    font-weight: 600;
    padding: 4px 0 4px 12px;
    border-left: 3px solid {C_ACCENT};
    background: transparent;
}}

QLabel#sectionHint {{
    color: {C_TEXT_MUTED};
    font-size: 11px;
    background: transparent;
    padding-left: 15px;
}}

QLabel#panelTitle {{
    color: {C_TEXT_SEC};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 4px 8px 6px 8px;
    background: transparent;
}}

QLabel#detailTitle {{
    color: {C_TEXT};
    font-size: 14px;
    font-weight: 600;
    padding: 6px 10px;
    background: {C_ACCENT_SOFT};
    border-radius: 8px;
    border-left: 3px solid {C_ACCENT};
}}

QLabel#formLabel {{
    color: {C_TEXT_MUTED};
    font-weight: 500;
    font-size: 11px;
    min-height: 14px;
    padding-left: 2px;
}}

QWidget#fieldCell {{
    background: {C_BG_SOFT};
    border: 1px solid {C_BORDER_LIGHT};
    border-radius: 10px;
}}

/* ---------- 导航列表 ---------- */
QListWidget#navList {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER_LIGHT};
    border-radius: 10px;
    padding: 4px;
    outline: none;
}}

QListWidget#navList::item {{
    border-radius: 8px;
    padding: 9px 12px;
    margin: 2px 0;
    min-height: 14px;
    font-size: 12px;
    color: {C_TEXT_SEC};
    border-left: 3px solid transparent;
}}

QListWidget#navList::item:selected {{
    background: {C_ACCENT_SOFT};
    color: {C_ACCENT};
    font-weight: 600;
    border-left: 3px solid {C_ACCENT};
}}

QListWidget#navList::item:hover:!selected {{
    background: #f1f5f9;
    color: {C_TEXT};
}}

QStackedWidget#detailStack {{
    background: transparent;
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    min-height: 18px;
    font-size: 12px;
    color: {C_TEXT};
    selection-background-color: {C_ACCENT_LIGHT};
}}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{
    border-color: #cbd5e1;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {C_ACCENT};
    background: #ffffff;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 16px;
    border: none;
    background: #f1f5f9;
    border-radius: 4px;
    margin: 2px;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {C_ACCENT_LIGHT};
}}

QComboBox::drop-down {{
    border: none;
    width: 22px;
}}

QComboBox QAbstractItemView {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    selection-background-color: {C_ACCENT_LIGHT};
    selection-color: {C_TEXT};
    padding: 4px;
    outline: none;
}}

QComboBox#tableCombo {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 0 6px;
    min-height: 26px;
    max-height: 28px;
    font-size: 11px;
}}

QComboBox#tableCombo::drop-down {{
    width: 16px;
    border-left: 1px solid {C_BORDER_LIGHT};
}}

QCheckBox {{
    spacing: 8px;
    color: {C_TEXT_SEC};
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    background: {C_SURFACE};
}}

QCheckBox::indicator:checked {{
    background: {C_ACCENT};
    border-color: {C_ACCENT};
}}

QCheckBox::indicator:hover {{
    border-color: {C_ACCENT};
}}

/* ---------- 按钮 ---------- */
QPushButton {{
    background: {C_SURFACE};
    color: {C_TEXT_SEC};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 12px;
    min-width: 60px;
    min-height: 30px;
}}

QPushButton:hover {{
    background: #f8fafc;
    border-color: #cbd5e1;
    color: {C_TEXT};
}}

QPushButton:pressed {{
    background: #f1f5f9;
}}

QPushButton#primaryButton {{
    background: {C_ACCENT};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background: {C_ACCENT_HOVER};
}}

QPushButton#dangerButton {{
    background: {C_DANGER_BG};
    color: {C_DANGER};
    border: 1px solid #fecaca;
}}

QPushButton#dangerButton:hover {{
    background: #fee2e2;
    border-color: #fca5a5;
}}

QPushButton#ghostButton {{
    background: {C_SURFACE};
    color: {C_ACCENT};
    border: 1px solid {C_ACCENT_LIGHT};
}}

QPushButton#ghostButton:hover {{
    background: {C_ACCENT_SOFT};
    border-color: #93c5fd;
}}

QPushButton#accentButton {{
    background: {C_ACCENT_SOFT};
    color: {C_ACCENT};
    border: 1px solid #bfdbfe;
    font-weight: 600;
}}

QPushButton#accentButton:hover {{
    background: {C_ACCENT_LIGHT};
}}

/* ---------- 表格 ---------- */
QTableWidget {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
    gridline-color: {C_BORDER_LIGHT};
    selection-background-color: {C_ACCENT_SOFT};
    selection-color: {C_TEXT};
    alternate-background-color: {C_BG_SOFT};
    font-size: 12px;
}}

QTableWidget#waypointTable {{
    border: 1px solid {C_BORDER};
    border-radius: 10px;
}}

QTableWidget#waypointTable QTableWidgetItem {{
    padding: 4px 8px;
}}

QTableWidget#waypointTable QWidget {{
    background: transparent;
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f8fafc, stop:1 #f1f5f9);
    color: {C_TEXT_MUTED};
    border: none;
    border-bottom: 2px solid {C_BORDER};
    border-right: 1px solid {C_BORDER_LIGHT};
    padding: 8px 6px;
    font-weight: 600;
    font-size: 11px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* ---------- 滚动条 / 分割条 ---------- */
QScrollArea, QScrollArea#waypointTableScroll {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 2px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: #94a3b8;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
}}

QSplitter::handle {{
    background: {C_BORDER_LIGHT};
    width: 3px;
    margin: 6px 4px;
    border-radius: 2px;
}}

QSplitter::handle:hover {{
    background: {C_ACCENT_LIGHT};
}}

/* ---------- 状态栏 ---------- */
QStatusBar {{
    background: {C_SURFACE};
    color: {C_TEXT_MUTED};
    border-top: 1px solid {C_BORDER};
    padding: 6px 16px;
    font-size: 11px;
}}

QMessageBox {{
    background: {C_SURFACE};
}}

QGroupBox {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px 12px 10px 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {C_TEXT_SEC};
    background: {C_SURFACE};
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    font = QFont("Microsoft YaHei UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)


def make_button(text: str, role: str = "default") -> QPushButton:
    btn = QPushButton(text)
    role_map = {
        "primary": "primaryButton",
        "danger": "dangerButton",
        "ghost": "ghostButton",
        "accent": "accentButton",
        "header_ghost": "headerGhostBtn",
        "header_primary": "headerPrimaryBtn",
    }
    if role in role_map:
        btn.setObjectName(role_map[role])
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("formLabel")
    return lbl


def make_card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    return frame


def make_toolbar_strip() -> QFrame:
    frame = QFrame()
    frame.setObjectName("toolBarStrip")
    return frame


def section_title(text: str, hint: str = "") -> QWidget:
    wrap = QWidget()
    layout = QVBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 6)
    layout.setSpacing(3)
    title = QLabel(text)
    title.setObjectName("sectionTitle")
    layout.addWidget(title)
    if hint:
        sub = QLabel(hint)
        sub.setObjectName("sectionHint")
        sub.setWordWrap(True)
        layout.addWidget(sub)
    return wrap


def header_bar(title: str, subtitle: str, save_cb, reload_cb) -> QFrame:
    bar = QFrame()
    bar.setObjectName("headerBar")
    bar.setFixedHeight(64)

    layout = QHBoxLayout(bar)
    layout.setContentsMargins(20, 10, 20, 10)
    layout.setSpacing(12)

    brand = QVBoxLayout()
    brand.setSpacing(1)
    t = QLabel(title)
    t.setObjectName("brandTitle")
    s = QLabel(subtitle)
    s.setObjectName("brandSubtitle")
    brand.addWidget(t)
    brand.addWidget(s)
    layout.addLayout(brand)
    layout.addStretch()

    reload_btn = make_button("重新加载", "header_ghost")
    reload_btn.clicked.connect(reload_cb)
    save_btn = make_button("保存配置", "header_primary")
    save_btn.clicked.connect(save_cb)
    layout.addWidget(reload_btn)
    layout.addWidget(save_btn)
    return bar
