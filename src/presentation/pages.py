from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .components import Card, PageHeader, StatusPill
from .theme import DANGER, MONO_FONT_FAMILY, SUCCESS, WARNING


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


class BasePage(QScrollArea):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setWidget(content)
        self.content_widget = content
        self.content_layout = layout

    def add_stretch(self):
        self.content_layout.addStretch(1)


class DashboardPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("仪表盘", "查看连接状态、控制自动交易，并快速进入配置与 Token 流程。")
        self.content_layout.addWidget(self.header)

        grid = QGridLayout()
        grid.setSpacing(16)

        server_card = Card()
        server_layout = QVBoxLayout(server_card)
        server_layout.setContentsMargins(16, 14, 16, 14)
        server_layout.setSpacing(8)
        server_title = QLabel("服务器", server_card)
        server_title.setObjectName("subtitle")
        self.server_status = StatusPill(server_card)
        server_layout.addWidget(server_title)
        server_layout.addWidget(self.server_status)
        grid.addWidget(server_card, 0, 0)

        trade_card = Card()
        trade_layout = QVBoxLayout(trade_card)
        trade_layout.setContentsMargins(16, 14, 16, 14)
        trade_layout.setSpacing(8)
        trade_title = QLabel("交易", trade_card)
        trade_title.setObjectName("subtitle")
        self.trade_status = StatusPill(trade_card)
        trade_layout.addWidget(trade_title)
        trade_layout.addWidget(self.trade_status)
        grid.addWidget(trade_card, 0, 1)

        action_card = Card()
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(16, 14, 16, 16)
        action_layout.setSpacing(10)
        action_title = QLabel("交易控制", action_card)
        action_title.setObjectName("subtitle")
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.start_btn = make_button("启动自动交易")
        self.stop_btn = make_button("停止自动交易", variant="danger")
        buttons.addWidget(self.start_btn, 1)
        buttons.addWidget(self.stop_btn, 1)
        action_layout.addWidget(action_title)
        action_layout.addLayout(buttons)
        self.auto_trade_checkbox = QCheckBox("启用自动交易（接收信号后自动下单）")
        action_layout.addWidget(self.auto_trade_checkbox)
        grid.addWidget(action_card, 1, 0, 1, 2)

        quick_card = Card()
        quick_layout = QGridLayout(quick_card)
        quick_layout.setContentsMargins(16, 14, 16, 16)
        quick_layout.setHorizontalSpacing(10)
        quick_layout.setVerticalSpacing(10)
        quick_title = QLabel("快捷操作", quick_card)
        quick_title.setObjectName("subtitle")
        self.config_btn = make_button("配置设置", variant="secondary")
        self.token_btn = make_button("Token 管理", variant="secondary")
        self.clear_logs_btn = make_button("清空日志", variant="secondary")
        self.quit_btn = make_button("退出客户端", variant="danger")
        quick_layout.addWidget(quick_title, 0, 0, 1, 3)
        quick_layout.addWidget(self.config_btn, 1, 0)
        quick_layout.addWidget(self.token_btn, 1, 1)
        quick_layout.addWidget(self.clear_logs_btn, 1, 2)
        quick_layout.addWidget(self.quit_btn, 2, 0, 1, 3)
        grid.addWidget(quick_card, 2, 0, 1, 2)

        self.content_layout.addLayout(grid)
        self.add_stretch()


class TokenPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("Token 管理", "申请、刷新并查看服务器审批状态。")
        self.content_layout.addWidget(self.header)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.token_description_edit = QLineEdit()
        self.token_description_edit.setPlaceholderText("例如：iTrader GUI Client")
        status_box = QWidget()
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        self.token_status_label = QLabel("未申请")
        self.token_status_label.setObjectName("tokenStatus")
        self.token_status_label.setWordWrap(True)
        self.token_status_label.setStyleSheet("color: %s;" % WARNING)
        status_layout.addWidget(self.token_status_label)
        form.addRow("申请说明:", self.token_description_edit)
        form.addRow("审批状态:", status_box)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.token_apply_btn = make_button("申请 Token")
        self.token_refresh_btn = make_button("刷新状态", variant="secondary")
        self.token_status_btn = make_button("查看状态", variant="secondary")
        self.token_status_btn.setEnabled(False)
        buttons.addWidget(self.token_apply_btn)
        buttons.addWidget(self.token_refresh_btn)
        buttons.addWidget(self.token_status_btn)
        buttons.addStretch(1)

        layout.addLayout(form)
        layout.addLayout(buttons)
        self.content_layout.addWidget(card)
        self.add_stretch()


class LogPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("交易日志", "实时查看客户端连接、信号、下单和异常信息。")
        self.content_layout.addWidget(self.header)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.clear_logs_btn = make_button("清空日志", variant="secondary")
        toolbar.addWidget(self.clear_logs_btn)
        toolbar.addStretch(1)
        self.content_layout.addLayout(toolbar)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "QTextEdit#logView { font-family: %s; font-size: 12px; }" % MONO_FONT_FAMILY
        )
        self.content_layout.addWidget(self.log_view, 1)


class SettingsPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("设置", "配置修改沿用现有 Preferences 对话框，保存后下次启动生效。")
        self.content_layout.addWidget(self.header)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(QLabel("设置项包括服务器地址、天勤账号、初始资金、交易品种和自动交易开关。", card))
        self.open_config_btn = make_button("打开配置设置")
        layout.addWidget(self.open_config_btn, 0, Qt.AlignLeft)
        layout.addStretch(1)
        self.content_layout.addWidget(card)

        info_card = Card()
        info_layout = QFormLayout(info_card)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setLabelAlignment(Qt.AlignRight)
        info_layout.setHorizontalSpacing(12)
        info_layout.setVerticalSpacing(10)
        info_layout.addRow("应用版本:", QLabel(__version__, info_card))
        info_layout.addRow("架构:", QLabel("Clean Architecture + PySide6", info_card))
        info_layout.addRow("平台:", QLabel("macOS / Windows", info_card))
        self.content_layout.addWidget(info_card)
        self.add_stretch()
