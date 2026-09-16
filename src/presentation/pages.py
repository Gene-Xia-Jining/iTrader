from typing import Optional, Callable
from PySide6.QtWidgets import QMessageBox

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

        grid = QGridLayout()
        grid.setSpacing(16)

        server_card = Card()
        server_layout = QVBoxLayout(server_card)
        server_layout.setContentsMargins(16, 14, 16, 14)
        server_layout.setSpacing(8)
        server_title = QLabel("服务器状态", server_card)
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
        quick_layout.addWidget(quick_title, 0, 0, 1, 3)
        quick_layout.addWidget(self.config_btn, 1, 0)
        quick_layout.addWidget(self.token_btn, 1, 1)
        quick_layout.addWidget(self.clear_logs_btn, 1, 2)
        grid.addWidget(quick_card, 1, 0, 1, 2)

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
        self.token_description_edit.setPlaceholderText("例如：iTrader 智能交易客户端")
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
        self.header = PageHeader("设置", "直接修改配置，保存后即时生效。")
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

        self.server_url_edit = QLineEdit()
        self.server_url_edit.setPlaceholderText("http://localhost:8000")
        form.addRow("服务器地址:", self.server_url_edit)

        self.tq_account_edit = QLineEdit()
        self.tq_account_edit.setPlaceholderText("天勤账号")
        form.addRow("天勤账号:", self.tq_account_edit)

        self.tq_password_edit = QLineEdit()
        self.tq_password_edit.setPlaceholderText("天勤密码")
        self.tq_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("天勤密码:", self.tq_password_edit)

        self.balance_edit = QLineEdit()
        self.balance_edit.setPlaceholderText("10000000")
        form.addRow("初始资金:", self.balance_edit)

        self.symbols_edit = QLineEdit()
        self.symbols_edit.setPlaceholderText("品种1,品种2,...")
        form.addRow("交易品种:", self.symbols_edit)

        layout.addLayout(form)

        self.save_btn = make_button("保存", variant="primary")
        layout.addWidget(self.save_btn, 0, Qt.AlignRight)
        self.save_btn.clicked.connect(self._on_save_clicked)

        layout.addStretch(1)
        self.content_layout.addWidget(card)

        # Fix: setContentsMargins must have 4 parameters
        # We'll set it in the BasePage, but ensure we don't have extra parameters
        # The BasePage already sets it correctly.

        # For compatibility, we keep the on_save callback to be set externally
        self.on_save = None  # type: Optional[Callable[[dict], None]]

        self.content_layout.addStretch(1)

    def _on_save_clicked(self):
        # Collect data
        data = {
            "server_url": self.server_url_edit.text().strip(),
            "tq_account": self.tq_account_edit.text().strip(),
            "tq_password": self.tq_password_edit.text(),
            "initial_balance": self.balance_edit.text().strip(),
            "symbols": self.symbols_edit.text().strip(),
        }

        # Validate
        if not data["server_url"]:
            QMessageBox.warning(self, "输入错误", "服务器地址不能为空")
            return
        if not data["tq_account"]:
            QMessageBox.warning(self, "输入错误", "天勤账号不能为空")
            return
        if not data["tq_password"]:
            QMessageBox.warning(self, "输入错误", "天勤密码不能为空")
            return
        if not data["initial_balance"]:
            QMessageBox.warning(self, "输入错误", "初始资金不能为空")
            return
        try:
            balance = float(data["initial_balance"])
            if balance <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "初始资金必须是正数")
            return
        if not data["symbols"]:
            QMessageBox.warning(self, "输入错误", "交易品种不能为空")
            return

        # Call the external save callback
        if self.on_save:
            self.on_save(data)
            QMessageBox.information(self, "保存成功", "配置已保存并生效")
        else:
            QMessageBox.warning(self, "错误", "保存回调未设置")
