from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)



class Card(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")


class StatusStatCard(Card):
    """状态指标卡：标题 + StatusPill 值行 + 说明行（如 服务器/交易状态）。"""

    def __init__(self, title: str, secondary: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        title_label = QLabel(title, self)
        title_label.setObjectName("dim")
        layout.addWidget(title_label)

        self._pill = StatusPill(self)
        layout.addWidget(self._pill)

        self.secondary_label = QLabel(secondary, self)
        self.secondary_label.setObjectName("dim")
        layout.addWidget(self.secondary_label)

    def set_status(self, text: str, color: str) -> None:
        self._pill.set_status(text, color)

    def set_secondary(self, text: str) -> None:
        self.secondary_label.setText(text)


class ValueStatCard(Card):
    """数值指标卡：标题 + 26px 大数字 + 说明行（如 账户资金/活跃品种）。"""

    def __init__(self, title: str, secondary: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        title_label = QLabel(title, self)
        title_label.setObjectName("dim")
        layout.addWidget(title_label)

        self.value_label = QLabel(self)
        self.value_label.setObjectName("metric")
        layout.addWidget(self.value_label)

        self.secondary_label = QLabel(secondary, self)
        self.secondary_label.setObjectName("dim")
        layout.addWidget(self.secondary_label)

    def set_value(self, text: str) -> None:
        self.value_label.setText(text)

    def set_secondary(self, text: str) -> None:
        self.secondary_label.setText(text)


class StatusPill(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("soft")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        dot = QLabel(self)
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            "background-color: #7a7a7a; border-radius: 5px; border: 0;"
        )
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
            dot.setStyleSheet(
                "background-color: %s; border-radius: 5px; border: 0;" % color
            )


class SidebarButton(QPushButton):
    def __init__(self, label: str, parent: Optional[QWidget] = None):
        # 文字只由内部 QLabel 渲染；若同时设置 QPushButton.text，按钮会把文字画两遍
        super().__init__(parent)
        self.setAccessibleName(label)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        text = QLabel(label, self)
        text.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        # 左 12px 与 QSS padding 对齐，避免文字紧贴按钮边缘
        layout.setContentsMargins(12, 0, 0, 0)
        layout.addWidget(text, 0, Qt.AlignLeft)
        layout.addStretch(1)


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str, parent: Optional[QWidget] = None):
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
