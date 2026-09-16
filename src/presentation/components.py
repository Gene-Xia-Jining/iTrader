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


class StatusPill(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("soft")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        dot = QLabel(self)
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            "background-color: #6c7086; border-radius: 4px; border: 0;"
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
            "background: transparent; color: %s; font-size: 14px; font-weight: 700;" % color
        )
        self.findChild(QLabel, "")
        dot = self.layout().itemAt(0).widget()
        if isinstance(dot, QLabel):
            dot.setStyleSheet(
                "background-color: %s; border-radius: 4px; border: 0;" % color
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
        layout.setContentsMargins(0, 0, 0, 0)
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
