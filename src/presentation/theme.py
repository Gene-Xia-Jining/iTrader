# Apple Design Language — design tokens mapped to PySide6 stylesheets.
# Source: Design.md (Apple-design-analysis)
# Interactive accent: Action Blue #0066cc (light) / Sky Link Blue #2997ff (dark).
# Surfaces: white / parchment / pearl (light) ↔ near-black tiles (dark).

APP_FONT_FAMILY = (
    "-apple-system, 'SF Pro Text', 'SF Pro Display', system-ui, "
    "'Segoe UI', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif"
)
DISPLAY_FONT_FAMILY = (
    "-apple-system, 'SF Pro Display', 'SF Pro Text', system-ui, "
    "'Segoe UI', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif"
)
MONO_FONT_FAMILY = "'SF Mono', Menlo, Consolas, 'Courier New', monospace"

# --- Light surfaces (default, Apple baseline) ---
CANVAS = "#ffffff"          # canvas
PARCHMENT = "#f5f5f7"       # canvas-parchment
PEARL = "#fafafc"           # surface-pearl
INK = "#1d1d1f"             # ink
INK_MUTED_80 = "#333333"    # ink-muted-80
INK_MUTED_48 = "#7a7a7a"    # ink-muted-48
HAIRLINE = "#e0e0e0"        # hairline
DIVIDER_SOFT = "#f0f0f0"    # divider-soft
DISABLED_TEXT = "#cccccc"   # body-muted
PRIMARY = "#0066cc"         # Action Blue
PRIMARY_FOCUS = "#0071e3"   # primary-focus
PRIMARY_HOVER = "#0071e3"
PRIMARY_TEXT = "#ffffff"    # on-primary
ON_DARK = "#ffffff"

# --- Dark surfaces ---
TILE_1 = "#272729"          # surface-tile-1
TILE_2 = "#2a2a2c"          # surface-tile-2
TILE_3 = "#252527"          # surface-tile-3
PRIMARY_ON_DARK = "#2997ff" # primary-on-dark (Sky Link Blue)

# --- Semantic / status colors ---
SUCCESS = "#34c759"         # iOS green
WARNING = "#e8a33d"         # amber
DANGER = "#e3342f"          # red
DANGER_HOVER = "#c5241f"

SPACING = 16
SECTION_GAP = 20
FIELD_GAP = 10
RADIUS = 18
BUTTON_HEIGHT = 36
CARD_PADDING = 20
SIDEBAR_WIDTH = 220


def status_color(text: str) -> str:
    """按状态文本返回语义色，适配浅色/深色画布。"""
    if "已通过" in text:
        return SUCCESS
    if "失败" in text or "错误" in text:
        return DANGER
    return WARNING


def log_colors(dark: bool) -> dict:
    """返回随主题适配的日志颜色映射，保证浅色/深色背景下都可读。"""
    if dark:
        return {
            "INFO": "#ffffff",
            "WARNING": "#ffd60a",
            "ERROR": "#ff453a",
            "SUCCESS": "#30d158",
        }
    return {
        "INFO": "#1d1d1f",
        "WARNING": "#b8780a",
        "ERROR": "#c5241f",
        "SUCCESS": "#1d9552",
    }


# =====================================================================
# Dark stylesheet (near-black surfaces, Sky Link Blue accent)
# =====================================================================
APP_QSS = """
* {
    font-family: -apple-system, 'SF Pro Text', 'SF Pro Display', system-ui, 'Segoe UI', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    letter-spacing: -0.1px;
}

QMainWindow, QDialog, QWidget {
    background-color: #272729;
    color: #ffffff;
}

QMenuBar, QStatusBar, QToolBar {
    background-color: #252527;
    border: 0;
}

QMenuBar {
    border-bottom: 1px solid #3a3a3c;
}

QStatusBar {
    border-top: 1px solid #3a3a3c;
}

QStatusBar QLabel {
    background: transparent;
    color: #cccccc;
    padding: 0 10px;
}

QToolBar {
    border-bottom: 1px solid #3a3a3c;
    padding: 10px;
}

QMenu {
    background-color: #252527;
    border: 1px solid #48484a;
    border-radius: 11px;
    padding: 6px;
}

QMenu::item {
    padding: 7px 20px;
    color: #ffffff;
    border-radius: 8px;
}

QMenu::item:selected {
    background-color: #48484a;
}

QMenu::separator {
    height: 1px;
    background-color: #3a3a3c;
    margin: 4px 10px;
}

QFrame#head {
    background-color: #252527;
    border-bottom: 1px solid #3a3a3c;
}

/* sidebar 与内容区同色，分隔线加深一档以保持分界 */
QFrame#sidebar {
    background-color: #272729;
    border-right: 1px solid #48484a;
}

QPushButton {
    background-color: #2997ff;
    color: #ffffff;
    border: 0;
    /* Qt 无法渲染超大圆角，36px 高按钮用半高 18px 得到胶囊形 */
    border-radius: 18px;
    padding: 10px 22px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover:enabled {
    background-color: #4aa3ff;
}

QPushButton:pressed:enabled {
    background-color: #2997ff;
}

QPushButton:disabled {
    background-color: #48484a;
    color: #86868b;
}

QPushButton[variant="secondary"] {
    background-color: transparent;
    color: #2997ff;
    border: 1px solid #48484a;
}

QPushButton[variant="secondary"]:hover:enabled {
    background-color: #303032;
    border-color: #86868b;
}

QPushButton[variant="secondary"]:pressed:enabled {
    background-color: #48484a;
}

QPushButton[variant="secondary"]:disabled {
    background-color: transparent;
    color: #86868b;
    border-color: #3a3a3c;
}

QPushButton[variant="danger"] {
    background-color: #ff453a;
}

QPushButton[variant="danger"]:hover:enabled {
    background-color: #ff5a50;
}

QPushButton[variant="danger"]:pressed:enabled {
    background-color: #ff453a;
}

QPushButton[variant="success"] {
    background-color: #30d158;
    color: #ffffff;
}

QPushButton[variant="success"]:hover:enabled {
    background-color: #46dd6a;
}

QPushButton[variant="success"]:pressed:enabled {
    background-color: #30d158;
}

QPushButton[variant="flat"] {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    padding: 8px 12px;
    min-height: 30px;
}

QPushButton[variant="flat"]:hover:enabled {
    background-color: #303032;
    color: #ffffff;
}

QFrame#sidebar QPushButton {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    min-height: 44px;
}

QFrame#sidebar QPushButton:hover {
    background-color: #303032;
    color: #ffffff;
}

QFrame#sidebar QPushButton:checked, QFrame#sidebar QPushButton[variant="selected"] {
    background-color: #48484a;
    color: #ffffff;
    border: 1px solid #48484a;
}

QFrame#sidebar QPushButton:checked QLabel, QFrame#sidebar QPushButton[variant="selected"] QLabel {
    color: #ffffff;
}

QLineEdit, QSpinBox, QTextEdit {
    background-color: #2a2a2c;
    color: #ffffff;
    border: 1px solid #48484a;
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: #2997ff;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #2997ff;
}

QLineEdit:disabled, QSpinBox:disabled, QTextEdit:disabled {
    color: #86868b;
    border-color: #3a3a3c;
}

QLineEdit::placeholder {
    color: #86868b;
}

/* QCheckBox / QRadioButton 不写 ::indicator 规则，保留 macOS 原生渲染 */
QCheckBox {
    color: #ffffff;
    spacing: 10px;
    min-height: 30px;
}

QCheckBox:disabled {
    color: #86868b;
}

QRadioButton {
    color: #ffffff;
    spacing: 10px;
    min-height: 30px;
}

QRadioButton:disabled {
    color: #86868b;
}

QFrame#card {
    background-color: #272729;
    border: 1px solid #3a3a3c;
    border-radius: 18px;
}

QFrame#soft {
    background-color: #2a2a2c;
    border: 1px solid #3a3a3c;
    border-radius: 16px;
}

/* 匹配到 QSS 的 QLabel 会以窗口底色填充背景，白色卡片内露出灰条，强制透明 */
QLabel#muted, QLabel#dim, QLabel#metricLabel, QLabel#title,
QLabel#subtitle, QLabel#metric, QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    background: transparent;
}

QLabel#muted, QLabel#dim {
    color: #cccccc;
}

QLabel#dim {
    color: #86868b;
    font-size: 13px;
}

QLabel#metricLabel {
    color: #cccccc;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
}

QFrame#divider {
    background-color: #3a3a3c;
    border: 0;
    max-height: 1px;
}

QLabel#title {
    color: #ffffff;
    font-family: -apple-system, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.4px;
}

QLabel#subtitle {
    color: #cccccc;
    font-size: 15px;
}

QLabel#metric {
    color: #ffffff;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.3px;
}

QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
}

QTextEdit#logView {
    background-color: #252527;
    border: 1px solid #3a3a3c;
    border-radius: 11px;
    padding: 12px;
    font-family: 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
    font-size: 13px;
}

QScrollArea {
    border: 0;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #252527;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #48484a;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #252527;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #48484a;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    border: 1px solid #3a3a3c;
    border-radius: 18px;
    margin-top: 12px;
    padding-top: 18px;
    background-color: #272729;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: #cccccc;
    font-weight: 600;
}
"""

# =====================================================================
# Light stylesheet (Apple baseline: white/parchment, Action Blue)
# =====================================================================
LIGHT_QSS = """
* {
    font-family: -apple-system, 'SF Pro Text', 'SF Pro Display', system-ui, 'Segoe UI', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    letter-spacing: -0.1px;
}

QMainWindow, QDialog, QWidget {
    background-color: #f5f5f7;
    color: #1d1d1f;
}

QMenuBar, QStatusBar, QToolBar {
    background-color: #ffffff;
    border: 0;
}

QMenuBar {
    border-bottom: 1px solid #f0f0f0;
}

QStatusBar {
    border-top: 1px solid #f0f0f0;
}

QStatusBar QLabel {
    background: transparent;
    color: #7a7a7a;
    padding: 0 10px;
}

QToolBar {
    border-bottom: 1px solid #f0f0f0;
    padding: 10px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 11px;
    padding: 6px;
}

QMenu::item {
    padding: 7px 20px;
    color: #1d1d1f;
    border-radius: 8px;
}

QMenu::item:selected {
    background-color: #f0f0f0;
}

QMenu::separator {
    height: 1px;
    background-color: #f0f0f0;
    margin: 4px 10px;
}

/* head 保持 chrome 白色表面，sidebar 与内容区同色，用发丝右边与内容区分界 */
QFrame#head {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
}

QFrame#sidebar {
    background-color: #f5f5f7;
    border-right: 1px solid #e0e0e0;
}

QPushButton {
    background-color: #0066cc;
    color: #ffffff;
    border: 0;
    /* Qt 无法渲染超大圆角，36px 高按钮用半高 18px 得到胶囊形 */
    border-radius: 18px;
    padding: 10px 22px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover:enabled {
    background-color: #0071e3;
}

QPushButton:pressed:enabled {
    background-color: #0066cc;
}

QPushButton:disabled {
    background-color: #e0e0e0;
    color: #cccccc;
}

QPushButton[variant="secondary"] {
    background-color: transparent;
    color: #0066cc;
    border: 1px solid #e0e0e0;
}

QPushButton[variant="secondary"]:hover:enabled {
    background-color: #f5f5f7;
    border-color: #7a7a7a;
}

QPushButton[variant="secondary"]:pressed:enabled {
    background-color: #f0f0f0;
}

QPushButton[variant="secondary"]:disabled {
    background-color: transparent;
    color: #cccccc;
    border-color: #f0f0f0;
}

QPushButton[variant="danger"] {
    background-color: #e3342f;
}

QPushButton[variant="danger"]:hover:enabled {
    background-color: #c5241f;
}

QPushButton[variant="danger"]:pressed:enabled {
    background-color: #e3342f;
}

QPushButton[variant="success"] {
    background-color: #34c759;
    color: #ffffff;
}

QPushButton[variant="success"]:hover:enabled {
    background-color: #30d158;
}

QPushButton[variant="success"]:pressed:enabled {
    background-color: #34c759;
}

QPushButton[variant="flat"] {
    background-color: transparent;
    color: #7a7a7a;
    border: 1px solid transparent;
    padding: 8px 12px;
    min-height: 30px;
}

QPushButton[variant="flat"]:hover:enabled {
    background-color: #f0f0f0;
    color: #1d1d1f;
}

QFrame#sidebar QPushButton {
    background-color: transparent;
    color: #7a7a7a;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    min-height: 44px;
}

QFrame#sidebar QPushButton:hover {
    background-color: #f0f0f0;
    color: #1d1d1f;
}

QFrame#sidebar QPushButton:checked, QFrame#sidebar QPushButton[variant="selected"] {
    background-color: #e0e0e0;
    color: #1d1d1f;
    border: 1px solid #e0e0e0;
}

QFrame#sidebar QPushButton:checked QLabel, QFrame#sidebar QPushButton[variant="selected"] QLabel {
    color: #1d1d1f;
}

QLineEdit, QSpinBox, QTextEdit {
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: #0066cc;
    selection-color: #ffffff;
}

QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #0066cc;
}

QLineEdit:disabled, QSpinBox:disabled, QTextEdit:disabled {
    color: #cccccc;
    border-color: #f0f0f0;
}

QLineEdit::placeholder {
    color: #cccccc;
}

/* QCheckBox / QRadioButton 不写 ::indicator 规则，保留 macOS 原生渲染 */
QCheckBox {
    color: #1d1d1f;
    spacing: 10px;
    min-height: 30px;
}

QCheckBox:disabled {
    color: #cccccc;
}

QRadioButton {
    color: #1d1d1f;
    spacing: 10px;
    min-height: 30px;
}

QRadioButton:disabled {
    color: #cccccc;
}

QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 18px;
}

QFrame#soft {
    background-color: #fafafc;
    border: 1px solid #e0e0e0;
    border-radius: 16px;
}

/* 匹配到 QSS 的 QLabel 会以窗口底色填充背景，白色卡片内露出灰条，强制透明 */
QLabel#muted, QLabel#dim, QLabel#metricLabel, QLabel#title,
QLabel#subtitle, QLabel#metric, QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    background: transparent;
}

QLabel#muted, QLabel#dim {
    color: #7a7a7a;
}

QLabel#dim {
    color: #7a7a7a;
    font-size: 13px;
}

QLabel#metricLabel {
    color: #7a7a7a;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
}

QFrame#divider {
    background-color: #f0f0f0;
    border: 0;
    max-height: 1px;
}

QLabel#title {
    color: #1d1d1f;
    font-family: -apple-system, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.4px;
}

QLabel#subtitle {
    color: #7a7a7a;
    font-size: 15px;
}

QLabel#metric {
    color: #1d1d1f;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.3px;
}

QLabel#tokenStatus, QLabel#serverStatus, QLabel#tradeStatus {
    color: #1d1d1f;
    font-size: 15px;
    font-weight: 600;
}

QTextEdit#logView {
    background-color: #fafafc;
    border: 1px solid #e0e0e0;
    border-radius: 11px;
    padding: 12px;
    font-family: 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
    font-size: 13px;
}

QScrollArea {
    border: 0;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #f5f5f7;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #d2d2d7;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #f5f5f7;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #d2d2d7;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    border: 1px solid #e0e0e0;
    border-radius: 18px;
    margin-top: 12px;
    padding-top: 18px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: #7a7a7a;
    font-weight: 600;
}
"""


def qss_for(dark: bool) -> str:
    """根据主题返回对应的全局样式表。"""
    return APP_QSS if dark else LIGHT_QSS