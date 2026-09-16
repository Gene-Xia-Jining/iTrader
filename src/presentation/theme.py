
BG = "#1e1e2e"
BG_ALT = "#181825"
BG_SOFT = "#2a2b3d"
CARD = "#313244"
BORDER = "#45475a"
BORDER_SOFT = "#3b3b4d"
TEXT = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
TEXT_DIM = "#6c7086"
PRIMARY = "#89b4fa"
PRIMARY_HOVER = "#a6c8ff"
PRIMARY_TEXT = "#111827"
SUCCESS = "#a6e3a1"
WARNING = "#f9e2af"
DANGER = "#f38ba8"
DANGER_HOVER = "#f5a7ba"

APP_FONT_FAMILY = "Inter, 'SF Pro Text', 'Segoe UI', Arial, 'PingFang SC', sans-serif"
MONO_FONT_FAMILY = "'SF Mono', Menlo, Consolas, 'Courier New', monospace"

SPACING = 12
SECTION_GAP = 16
FIELD_GAP = 8
RADIUS = 10
BUTTON_HEIGHT = 36
CARD_PADDING = 16
SIDEBAR_WIDTH = 220


def status_color(text: str) -> str:
    if "已通过" in text:
        return SUCCESS
    if "失败" in text or "错误" in text:
        return DANGER
    return WARNING


def log_colors(dark: bool) -> dict:
    """返回随主题适配的日志颜色映射，保证浅色/深色背景下都可读。"""
    if dark:
        return {
            "INFO": "#cdd6f4",
            "WARNING": "#f9e2af",
            "ERROR": "#f38ba8",
            "SUCCESS": "#a6e3a1",
        }
    return {
        "INFO": "#1e1e2e",
        "WARNING": "#b8780a",
        "ERROR": "#c5241f",
        "SUCCESS": "#1d9552",
    }


APP_QSS = """
* {
    font-family: Inter, 'SF Pro Text', 'Segoe UI', Arial, 'PingFang SC', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QMenuBar, QStatusBar, QToolBar {
    background-color: #181825;
    border: 0;
}

QMenuBar {
    border-bottom: 1px solid #3b3b4d;
}

QStatusBar {
    border-top: 1px solid #3b3b4d;
}

QStatusBar QLabel {
    background: transparent;
    color: #a6adc8;
    padding: 0 8px;
}

QToolBar {
    border-bottom: 1px solid #3b3b4d;
    padding: 8px;
}

QMenu {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 6px 18px;
    color: #cdd6f4;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #45475a;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #3b3b4d;
    margin: 4px 8px;
}

QFrame#sidebar {
    background-color: #181825;
    border-right: 1px solid #3b3b4d;
}

QPushButton {
    background-color: #89b4fa;
    color: #111827;
    border: 0;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover:enabled {
    background-color: #a6c8ff;
}

QPushButton:pressed:enabled {
    background-color: #89b4fa;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton[variant="secondary"] {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
}

QPushButton[variant="secondary"]:hover:enabled {
    background-color: #2a2b3d;
    border-color: #6c7086;
}

QPushButton[variant="secondary"]:pressed:enabled {
    background-color: #45475a;
}

QPushButton[variant="secondary"]:disabled {
    background-color: #313244;
    color: #6c7086;
    border-color: #3b3b4d;
}

QPushButton[variant="danger"] {
    background-color: #f38ba8;
}

QPushButton[variant="danger"]:hover:enabled {
    background-color: #f5a7ba;
}

QPushButton[variant="danger"]:pressed:enabled {
    background-color: #f38ba8;
}

QPushButton[variant="success"] {
    background-color: #a6e3a1;
    color: #111827;
}

QPushButton[variant="success"]:hover:enabled {
    background-color: #b9f0b5;
}

QPushButton[variant="success"]:pressed:enabled {
    background-color: #a6e3a1;
}

QPushButton[variant="flat"] {
    background-color: transparent;
    color: #a6adc8;
    border: 1px solid transparent;
    padding: 6px 10px;
    min-height: 30px;
}

QPushButton[variant="flat"]:hover:enabled {
    background-color: #2a2b3d;
    color: #cdd6f4;
    border-color: #3b3b4d;
}

QFrame#sidebar QPushButton {
    background-color: transparent;
    color: #a6adc8;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 12px;
    text-align: left;
    min-height: 44px;
}

QFrame#sidebar QPushButton:hover {
    background-color: #2a2b3d;
    color: #cdd6f4;
}

QFrame#sidebar QPushButton:checked, QFrame#sidebar QPushButton[variant="selected"] {
    background-color: #2a2b3d;
    color: #cdd6f4;
    border: 1px solid #3b3b4d;
}

QFrame#sidebar QPushButton:checked QLabel, QFrame#sidebar QPushButton[variant="selected"] QLabel {
    color: #cdd6f4;
}

QLineEdit, QSpinBox, QTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #89b4fa;
    selection-color: #111827;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #89b4fa;
}

QLineEdit:disabled, QSpinBox:disabled, QTextEdit:disabled {
    color: #6c7086;
    border-color: #3b3b4d;
}

QLineEdit::placeholder {
    color: #6c7086;
}

QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
    min-height: 30px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #45475a;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QCheckBox:disabled {
    color: #6c7086;
}

QFrame#card {
    background-color: #313244;
    border: 1px solid #3b3b4d;
    border-radius: 10px;
}

QFrame#soft {
    background-color: #181825;
    border: 1px solid #3b3b4d;
    border-radius: 10px;
}

QLabel#muted, QLabel#dim {
    color: #a6adc8;
}

QLabel#dim {
    color: #6c7086;
    font-size: 12px;
}

QLabel#title {
    color: #cdd6f4;
    font-size: 18px;
    font-weight: 700;
}

QLabel#subtitle {
    color: #a6adc8;
    font-size: 13px;
}

QLabel#metric {
    color: #cdd6f4;
    font-size: 20px;
    font-weight: 700;
}

QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: 700;
}

QTextEdit#logView {
    background-color: #181825;
    border: 1px solid #3b3b4d;
    border-radius: 8px;
    padding: 8px;
    font-family: 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
    font-size: 12px;
}

QScrollArea {
    border: 0;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #181825;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #181825;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    border: 1px solid #3b3b4d;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 18px;
    background-color: #313244;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #a6adc8;
    font-weight: 600;
}
"""

LIGHT_QSS = """
* {
    font-family: Inter, 'SF Pro Text', 'Segoe UI', Arial, 'PingFang SC', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog, QWidget {
    background-color: #f4f4f8;
    color: #1e1e2e;
}

QMenuBar, QStatusBar, QToolBar {
    background-color: #ffffff;
    border: 0;
}

QMenuBar {
    border-bottom: 1px solid #ececf0;
}

QStatusBar {
    border-top: 1px solid #ececf0;
}

QStatusBar QLabel {
    background: transparent;
    color: #585a72;
    padding: 0 8px;
}

QToolBar {
    border-bottom: 1px solid #ececf0;
    padding: 8px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e3e3e9;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 6px 18px;
    color: #1e1e2e;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #e8e8f0;
    color: #1e1e2e;
}

QMenu::separator {
    height: 1px;
    background-color: #ececf0;
    margin: 4px 8px;
}

QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #ececf0;
}

QPushButton {
    background-color: #4c7bf3;
    color: #ffffff;
    border: 0;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover:enabled {
    background-color: #3a68de;
}

QPushButton:pressed:enabled {
    background-color: #4c7bf3;
}

QPushButton:disabled {
    background-color: #e3e3e9;
    color: #8a8a98;
}

QPushButton[variant="secondary"] {
    background-color: #ffffff;
    color: #1e1e2e;
    border: 1px solid #e3e3e9;
}

QPushButton[variant="secondary"]:hover:enabled {
    background-color: #f4f4f8;
    border-color: #8a8a98;
}

QPushButton[variant="secondary"]:pressed:enabled {
    background-color: #e8e8f0;
}

QPushButton[variant="secondary"]:disabled {
    background-color: #ffffff;
    color: #8a8a98;
    border-color: #ececf0;
}

QPushButton[variant="danger"] {
    background-color: #e3342f;
    color: #ffffff;
}

QPushButton[variant="danger"]:hover:enabled {
    background-color: #c5241f;
}

QPushButton[variant="danger"]:pressed:enabled {
    background-color: #e3342f;
}

QPushButton[variant="success"] {
    background-color: #22a860;
    color: #ffffff;
}

QPushButton[variant="success"]:hover:enabled {
    background-color: #1d9552;
}

QPushButton[variant="success"]:pressed:enabled {
    background-color: #22a860;
}

QPushButton[variant="flat"] {
    background-color: transparent;
    color: #585a72;
    border: 1px solid transparent;
    padding: 6px 10px;
    min-height: 30px;
}

QPushButton[variant="flat"]:hover:enabled {
    background-color: #e8e8f0;
    color: #1e1e2e;
    border-color: #e3e3e9;
}

QFrame#sidebar QPushButton {
    background-color: transparent;
    color: #585a72;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 12px;
    text-align: left;
    min-height: 44px;
}

QFrame#sidebar QPushButton:hover {
    background-color: #e8e8f0;
    color: #1e1e2e;
}

QFrame#sidebar QPushButton:checked, QFrame#sidebar QPushButton[variant="selected"] {
    background-color: #e8e8f0;
    color: #1e1e2e;
    border: 1px solid #e3e3e9;
}

QFrame#sidebar QPushButton:checked QLabel, QFrame#sidebar QPushButton[variant="selected"] QLabel {
    color: #1e1e2e;
}

QLineEdit, QSpinBox, QTextEdit {
    background-color: #ffffff;
    color: #1e1e2e;
    border: 1px solid #e3e3e9;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #4c7bf3;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #4c7bf3;
}

QLineEdit:disabled, QSpinBox:disabled, QTextEdit:disabled {
    color: #8a8a98;
    border-color: #ececf0;
}

QLineEdit::placeholder {
    color: #8a8a98;
}

QCheckBox {
    color: #1e1e2e;
    spacing: 8px;
    min-height: 30px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #e3e3e9;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4c7bf3;
    border-color: #4c7bf3;
}

QCheckBox:disabled {
    color: #8a8a98;
}

QFrame#card {
    background-color: #ffffff;
    border: 1px solid #ececf0;
    border-radius: 10px;
}

QFrame#soft {
    background-color: #f4f4f8;
    border: 1px solid #ececf0;
    border-radius: 10px;
}

QLabel#muted, QLabel#dim {
    color: #585a72;
}

QLabel#dim {
    color: #8a8a98;
    font-size: 12px;
}

QLabel#title {
    color: #1e1e2e;
    font-size: 18px;
    font-weight: 700;
}

QLabel#subtitle {
    color: #585a72;
    font-size: 13px;
}

QLabel#metric {
    color: #1e1e2e;
    font-size: 20px;
    font-weight: 700;
}

QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    color: #1e1e2e;
    font-size: 14px;
    font-weight: 700;
}

QTextEdit#logView {
    background-color: #f4f4f8;
    border: 1px solid #ececf0;
    border-radius: 8px;
    padding: 8px;
    font-family: 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
    font-size: 12px;
}

QScrollArea {
    border: 0;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #ffffff;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #c8c8d0;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #ffffff;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #c8c8d0;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    border: 1px solid #ececf0;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 18px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #585a72;
    font-weight: 600;
}
"""


def qss_for(dark: bool) -> str:
    """根据主题返回对应的全局样式表。"""
    return APP_QSS if dark else LIGHT_QSS
