# iTrader — Design Tokens (PySide6 QSS, Apple design language)

> 来源：`src/presentation/theme.py`（DESIGN.md 的 Qt 落地）+ `DESIGN.md`（Apple-design-analysis）。默认浅色主题，深色可切换。

## Compact Token Summary

### Light (default)
| Token | Value |
|---|---|
| canvas / content bg | `#f5f5f7` (parchment) |
| card / sidebar / menu / statusbar bg | `#ffffff` |
| soft pill bg (StatusPill) | `#fafafc` (pearl) |
| ink / body text | `#1d1d1f` |
| ink-muted-80 | `#333333` |
| muted / subtitle / sidebar item | `#7a7a7a` |
| hairline / input border | `#e0e0e0` |
| divider-soft / menu hover | `#f0f0f0` |
| disabled text | `#cccccc` |
| primary (Action Blue) | `#0066cc` |
| primary hover/focus | `#0071e3` |
| on-primary | `#ffffff` |

### Dark
| Token | Value |
|---|---|
| content bg | `#272729` (tile-1) |
| sidebar / menu / statusbar bg | `#252527` (tile-3) |
| input bg | `#2a2a2c` (tile-2) |
| card bg | `#272729` |
| text | `#ffffff` |
| muted | `#cccccc` |
| dim | `#86868b` |
| border / hover | `#3a3a3c` / `#48484a` |
| primary on dark (Sky Link Blue) | `#2997ff`, hover `#4aa3ff` |

### Semantic status
`SUCCESS #34c759` · `WARNING #e8a33d` · `DANGER #e3342f` (hover `#c5241f`) · 运行时状态点/字：绿 `#2ecc71` / 红 `#e74c3c`；日志色：浅色 INFO `#1d1d1f` / WARN `#b8780a` / ERROR `#c5241f` / SUCCESS `#1d9552`，深色 `#ffffff` / `#ffd60a` / `#ff453a` / `#30d158`；success 按钮深色 `#30d158`。

### Typography
- 字体栈：`-apple-system, 'SF Pro Text', 'SF Pro Display', system-ui, 'Segoe UI', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif`；等宽：`'SF Mono', Menlo, Consolas, monospace`
- 全局 15px / letter-spacing -0.1px；title 22px/600/-0.4px；subtitle 15px muted；metric 26px/600；dim 13px；日志 12-13px 等宽
- 字重梯度：400 / 600（按钮 600）；无 500

### Geometry
- 圆角：卡片/GroupBox 18px；输入框 8px；按钮/StatusPill/搜索 9999px 胶囊；菜单 11px；复选框 5px；侧边栏项 8px
- 按钮高 36px（min），padding 10px 22px；flat 30px；侧边栏项 44px
- 间距常量：SPACING 16 · SECTION_GAP 20 · FIELD_GAP 10 · CARD_PADDING 20 · SIDEBAR_WIDTH 220(实际 240) · 页面边距 24
- 窗口：1180×760 默认，960×620 最小

## Part 2 — Raw QSS source
### LIGHT_QSS（默认浅色，`src/presentation/theme.py`）

```css

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

QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #f0f0f0;
}

QPushButton {
    background-color: #0066cc;
    color: #ffffff;
    border: 0;
    border-radius: 9999px;
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
    background-color: #f0f0f0;
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

QCheckBox {
    color: #1d1d1f;
    spacing: 10px;
    min-height: 30px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #e0e0e0;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0066cc;
    border-color: #0066cc;
}

QCheckBox:disabled {
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
    border-radius: 9999px;
}

QLabel#muted, QLabel#dim {
    color: #7a7a7a;
}

QLabel#dim {
    color: #7a7a7a;
    font-size: 13px;
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
```

### APP_QSS（深色，`src/presentation/theme.py`）

```css

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

QFrame#sidebar {
    background-color: #252527;
    border-right: 1px solid #3a3a3c;
}

QPushButton {
    background-color: #2997ff;
    color: #ffffff;
    border: 0;
    border-radius: 9999px;
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
    background-color: #3a3a3c;
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

QCheckBox {
    color: #ffffff;
    spacing: 10px;
    min-height: 30px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #48484a;
    background-color: #2a2a2c;
}

QCheckBox::indicator:checked {
    background-color: #2997ff;
    border-color: #2997ff;
}

QCheckBox:disabled {
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
    border-radius: 9999px;
}

QLabel#muted, QLabel#dim {
    color: #cccccc;
}

QLabel#dim {
    color: #86868b;
    font-size: 13px;
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
```
