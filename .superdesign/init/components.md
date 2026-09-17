# iTrader — Shared UI Components (PySide6 / Qt Widgets)

> 桌面应用（非 Web 前端）。以下为共享 UI 原语的完整源码，样式由 `theme.py` 的全局 QSS 驱动（objectName / dynamic property 选择器）。

## make_button (factory)
- File: `src/presentation/pages.py`
- 创建变体按钮：`variant` 属性可为 `""`(primary) / `secondary` / `danger` / `success` / `flat`，样式在 QSS 中定义。

```python
def make_button(text: str, variant: str = "", style: str = "", object_name: str = ""):
    from PySide6.QtWidgets import QPushButton
    button = QPushButton(text)
    if variant:
        button.setProperty("variant", variant)
    if style:
        button.setStyleSheet(style)
    if object_name:
        button.setObjectName(object_name)
    return button
```

## Card
- File: `src/presentation/components.py`
- 基础卡片容器。QSS `QFrame#card`：白底 / 1px hairline 边框 / 18px 圆角（深色下为 tile 底色）。

```python
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
```

## StatusPill
- File: `src/presentation/components.py`
- 状态胶囊：QSS `QFrame#soft`（pearl 底 + hairline 边框 + 全圆角胶囊），内含 10px 圆点 + 状态文字。`set_status(text, color)` 同时染点和字。

```python
class StatusPill(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("soft")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        dot = QLabel(self)
        dot.setFixedSize(10, 10)
        dot.setStyleSheet("background-color: #7a7a7a; border-radius: 5px; border: 0;")
        self.value_label = QLabel(self)
        self.value_label.setObjectName("serverStatus")
        self.value_label.setMinimumWidth(48)

        layout.addWidget(dot)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_status(self, text: str, color: str) -> None:
        self.value_label.setText(text)
        self.value_label.setStyleSheet(
            "background: transparent; color: %s; font-size: 15px; font-weight: 600;" % color
        )
        dot = self.layout().itemAt(0).widget()
        if isinstance(dot, QLabel):
            dot.setStyleSheet("background-color: %s; border-radius: 5px; border: 0;" % color)
```

## SidebarButton
- File: `src/presentation/components.py`
- 侧边栏导航按钮（checkable）。文字由内部 QLabel 渲染。QSS：透明底灰字，hover 浅灰底，checked 状态 `#f0f0f0` 底 + hairline 边框，8px 圆角，min-height 44px。

```python
class SidebarButton(QPushButton):
    def __init__(self, label: str, parent=None):
        # 文字只由内部 QLabel 渲染；若同时设置 QPushButton.text，按钮会把文字画两遍
        super().__init__(parent)
        self.setAccessibleName(label)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        text = QLabel(label, self)
        text.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(text, 0, Qt.AlignLeft)
        layout.addStretch(1)
```

## PageHeader
- File: `src/presentation/components.py`
- 页头：大标题（QSS `QLabel#title`：22px / 600 / -0.4px）+ 副标题（`QLabel#subtitle`：15px / muted）。

```python
class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("title")
        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
```

## ServerUrlTestRow
- File: `src/presentation/pages.py`
- 服务器地址输入行：圆形「?」帮助按钮（20px，蓝字胶囊描边）+ QLineEdit（占位 `http://localhost:8000`）+ 「测试连接」secondary 按钮；下方可显隐的结果标签（成功绿 / 失败红 / 进行中琥珀）。

```python
class ServerUrlTestRow(QWidget):
    def __init__(self, initial: str = "", parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.help_btn.setStyleSheet(
            "QToolButton {"
            "color: #0066cc; font-weight: 600; font-size: 14px;"
            "border: 1px solid #e0e0e0; border-radius: 9999px;"
            "background: transparent;"
            "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
            "}"
            "QToolButton:hover { background: #f0f0f0; }"
            "QToolButton:pressed { background: #e0e0e0; }"
        )
        self.help_btn.clicked.connect(self._show_help)
        row.addWidget(self.help_btn)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:8000")
        if initial:
            self.url_edit.setText(initial)
        self.test_btn = make_button("测试连接", variant="secondary")
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.test_btn)
        outer.addLayout(row)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        outer.addWidget(self.result_label)
```

## QLineEdit / QCheckBox 视觉规格（来自 QSS）
- 输入框：白底、1px `#e0e0e0` 边框、8px 圆角、padding 9px 12px、focus 边框变 `#0066cc`。
- 复选框：18px 指示器、5px 圆角、选中填充 Action Blue。
