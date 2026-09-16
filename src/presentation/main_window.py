from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..domain.entities import TradingConfiguration
from .components import SidebarButton
from .pages import AccountPage, DashboardPage, make_button, LogPage, ServerUrlTestRow, SettingsPage, TokenPage
from .theme import qss_for, status_color
from .viewmodels import ConfigDialogViewModel, MainViewModel


DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 16px;
    font-weight: bold;
    color: #bac2de;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #7f849c;
}
QPushButton#danger {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#danger:hover {
    background-color: #eba0ac;
}
QLineEdit, QTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 8px;
    color: #cdd6f4;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #89b4fa;
}
QLabel {
    color: #bac2de;
}
QCheckBox {
    color: #bac2de;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #585b70;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #a6e3a1;
    border: 1px solid #a6e3a1;
}
QMenuBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
}
QMenuBar::item {
    padding: 6px 14px;
    background: transparent;
    color: #bac2de;
}
QMenuBar::item:selected {
    background-color: #45475a;
    color: #ffffff;
}
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 20px;
    color: #cdd6f4;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #45475a;
}
QStatusBar {
    background-color: #181825;
    color: #bac2de;
    border-top: 1px solid #313244;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
}
QDialog {
    background-color: #1e1e2e;
}
QMessageBox {
    background-color: #1e1e2e;
}
"""


class ConfigDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        config: TradingConfiguration,
    ):
        super().__init__(parent)
        self.setWindowTitle("配置设置")
        self.setModal(True)
        self.resize(480, 420)
        self._vm = ConfigDialogViewModel(config, self)
        self._result: Optional[dict] = None
        self._build_ui()
        self._vm.validated.connect(self._on_validated)
        self._vm.cancelled.connect(self._on_cancelled)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.server_test = ServerUrlTestRow(self._vm.server_url)
        self.server_url_edit = self.server_test.url_edit
        form.addRow("服务器地址:", self.server_test)

        self.tq_account_edit = QLineEdit(self._vm.tq_account)
        form.addRow("天勤账号:", self.tq_account_edit)

        self.tq_password_edit = QLineEdit(self._vm.tq_password)
        self.tq_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("天勤密码:", self.tq_password_edit)

        self.balance_edit = QLineEdit(str(self._vm.initial_balance))
        self.balance_edit.setPlaceholderText("10000000")
        form.addRow("初始资金:", self.balance_edit)

        self.symbols_edit = QLineEdit(self._vm.symbols_text())
        self.symbols_edit.setPlaceholderText("品种1,品种2,...")
        symbols_hint = QLabel("(逗号分隔，例如: SHFE.au2510,INE.sc2510)")
        symbols_hint.setStyleSheet("color: #6c7086; font-size: 11px;")
        form.addRow("交易品种:", self.symbols_edit)
        form.addRow("", symbols_hint)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.Ok).clicked.connect(self._submit)
        buttons.button(QDialogButtonBox.Cancel).clicked.connect(self._cancel)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _submit(self):
        ok, msg = self._vm.submit(
            server_url=self.server_url_edit.text().strip(),
            tq_account=self.tq_account_edit.text(),
            tq_password=self.tq_password_edit.text(),
            initial_balance_str=self.balance_edit.text().strip(),
            symbols_str=self.symbols_edit.text(),
        )
        if not ok:
            QMessageBox.warning(self, "输入错误", msg)

    def _cancel(self):
        self._vm.cancel()

    def _on_validated(self, data: dict):
        self._result = data
        self.accept()

    def _on_cancelled(self):
        self._result = None
        self.reject()

    @property
    def result_dict(self) -> Optional[dict]:
        return self._result


class MainWindow(QMainWindow):
    def __init__(
        self,
        vm: MainViewModel,
        on_toggle_auto_trade,
        on_open_config,
        on_open_token,
        on_clear_logs,
        on_show_about,
        on_quit,
        on_save_config,
        on_save_account=None,
        on_test_server=None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._vm = vm
        self._on_toggle_auto_trade = on_toggle_auto_trade
        self._on_open_config = on_open_config
        self._on_open_token = on_open_token
        self._on_clear_logs = on_clear_logs
        self._on_show_about = on_show_about
        self._on_quit = on_quit
        self._on_save_config = on_save_config
        self._on_save_account = on_save_account
        self._on_test_server = on_test_server

        self.setWindowTitle("iTrader 智能交易客户端")
        self.resize(1180, 760)
        self.setMinimumSize(QSize(960, 620))
        self._dark = True
        self.setStyleSheet(qss_for(self._dark))
        self._build_menubar()
        self._build_ui()
        self._build_statusbar()
        self._bind_vm()

    def _build_menubar(self):
        bar = self.menuBar()

        file_menu = QMenu("文件", self)
        open_config_action = QAction("配置设置...", self)
        open_config_action.setShortcut("Ctrl+,")
        open_config_action.triggered.connect(self._on_open_config)
        file_menu.addAction(open_config_action)
        open_token_action = QAction("Token 申请与审批...", self)
        open_token_action.triggered.connect(self._on_open_token)
        file_menu.addAction(open_token_action)
        file_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self._on_quit)
        file_menu.addAction(quit_action)
        bar.addMenu(file_menu)

        view_menu = QMenu("视图", self)
        clear_logs_action = QAction("清空日志", self)
        clear_logs_action.triggered.connect(self._on_clear_logs)
        view_menu.addAction(clear_logs_action)
        bar.addMenu(view_menu)

        help_menu = QMenu("帮助", self)
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
        bar.addMenu(help_menu)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        head = QFrame()
        head.setObjectName("head")
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(20, 14, 20, 14)
        head_layout.setSpacing(12)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        brand_label = QLabel("iTrader", head)
        brand_label.setObjectName("title")
        brand_sub = QLabel("智能交易客户端", head)
        brand_sub.setObjectName("subtitle")
        brand.addWidget(brand_label)
        brand.addWidget(brand_sub)
        head_layout.addLayout(brand)
        head_layout.addStretch(1)
        self._head_auto_btn = make_button("", variant="")
        self._head_auto_btn.setToolTip("点击启动/停止自动交易")
        self._head_auto_btn.clicked.connect(lambda: self._on_toggle_auto_trade(not self._vm.tradingActive))
        self._sync_auto_trade_button(self._vm.tradingActive)
        head_layout.addWidget(self._head_auto_btn)
        self._head_theme_btn = make_button("", variant="secondary")
        self._head_theme_btn.setCheckable(True)
        self._head_theme_btn.clicked.connect(self._toggle_theme)
        self._sync_theme_button(self._dark)
        head_layout.addWidget(self._head_theme_btn)
        self._head_quit_btn = make_button("退出", variant="danger")
        self._head_quit_btn.clicked.connect(self._on_quit)
        head_layout.addWidget(self._head_quit_btn)
        layout.addWidget(head)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
        sidebar_layout.setSpacing(10)

        nav = QVBoxLayout()
        nav.setSpacing(6)
        self.dashboard_btn = SidebarButton("仪表盘", sidebar)
        self.token_btn = SidebarButton("Token 管理", sidebar)
        self.log_btn = SidebarButton("交易日志", sidebar)
        self.account_btn = SidebarButton("交易账号", sidebar)
        self.settings_btn = SidebarButton("设置", sidebar)
        for button in (
            self.dashboard_btn,
            self.token_btn,
            self.log_btn,
            self.account_btn,
            self.settings_btn,
        ):
            nav.addWidget(button)
        self.dashboard_btn.setChecked(True)
        self.dashboard_btn.clicked.connect(lambda: self._switch_page(0))
        self.token_btn.clicked.connect(lambda: self._switch_page(1))
        self.log_btn.clicked.connect(lambda: self._switch_page(2))
        self.account_btn.clicked.connect(lambda: self._switch_page(3))
        self.settings_btn.clicked.connect(lambda: self._switch_page(4))
        sidebar_layout.addLayout(nav)
        sidebar_layout.addStretch(1)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.token_page = TokenPage()
        self.log_page = LogPage()
        self.account_page = AccountPage()
        self.settings_page = SettingsPage()
        # Connect settings page save callback
        self.settings_page.on_save = self._on_save_config
        self.settings_page.server_test.on_test = self._on_test_server
        self.settings_page.set_config(self._vm.config)
        # Connect account page save callback
        self.account_page.on_save = self._on_save_account
        self.account_page.set_config(self._vm.config)
        for page in (
            self.dashboard_page,
            self.token_page,
            self.log_page,
            self.account_page,
            self.settings_page,
        ):
            self.stack.addWidget(page)
        self.stack.setCurrentIndex(0)

        self.dashboard_page.config_btn.clicked.connect(lambda: self._switch_page(4))
        self.dashboard_page.token_btn.clicked.connect(lambda: self._switch_page(1))
        self.dashboard_page.clear_logs_btn.clicked.connect(self._on_clear_logs)

        self.token_page.token_apply_btn.clicked.connect(self._on_apply_token)
        self.token_page.token_refresh_btn.clicked.connect(self._on_refresh_token)
        self.token_page.token_status_btn.clicked.connect(lambda: QMessageBox.information(self, "Token 审批状态", self.token_page.token_status_label.text()))
        self.token_page.token_status_btn.setEnabled(False)

        self.log_page.clear_logs_btn.clicked.connect(self._on_clear_logs)
        # Settings page now uses embedded form, no open_config_btn
        # self.settings_page.open_config_btn.clicked.connect(self._on_open_config)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.stack, 1)
        layout.addWidget(body, 1)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.dashboard_btn.setChecked(index == 0)
        self.token_btn.setChecked(index == 1)
        self.log_btn.setChecked(index == 2)
        self.account_btn.setChecked(index == 3)
        self.settings_btn.setChecked(index == 4)

    def _build_statusbar(self):
        bar = self.statusBar()
        self._status_text = QLabel("就绪")
        bar.addWidget(self._status_text, 1)

    def _bind_vm(self):
        self._vm.serverStatusChanged.connect(self._on_server_status_changed)
        self._vm.themeChanged.connect(self._on_theme_changed)
        self._vm.serverStatusColorChanged.connect(self._on_server_status_color_changed)
        self._vm.tradingStatusChanged.connect(self._on_trade_status_changed)
        self._vm.tradingStatusColorChanged.connect(self._on_trade_status_color_changed)
        self._vm.logMessage.connect(self._append_log)
        self._vm.configChanged.connect(
            lambda: self.settings_page.set_config(self._vm.config)
        )
        self._vm.configChanged.connect(
            lambda: self.account_page.set_config(self._vm.config)
        )
        self._on_server_status_changed(self._vm.serverStatus)
        self._on_server_status_color_changed(self._vm.serverStatusColor)
        self._on_trade_status_changed(self._vm.tradingStatus)
        self._on_trade_status_color_changed(self._vm.tradingStatusColor)

    def _on_server_status_changed(self, value: str):
        self.dashboard_page.server_status.set_status(value, self._vm.serverStatusColor)

    def _on_server_status_color_changed(self, color: str):
        self.dashboard_page.server_status.set_status(self._vm.serverStatus, color)

    def _on_trade_status_changed(self, value: str):
        self.dashboard_page.trade_status.set_status(value, self._vm.tradingStatusColor)
        self._status_text.setText(f"交易状态: {value}")
        self._sync_auto_trade_button(self._vm.tradingActive)

    def _on_trade_status_color_changed(self, color: str):
        self.dashboard_page.trade_status.set_status(self._vm.tradingStatus, color)

    def set_token_status(self, text: str):
        self.token_page.token_status_label.setText(text)
        self.token_page.token_status_label.setStyleSheet(f"color: {status_color(text)};")
        if "已通过" in text:
            self.token_page.token_status_btn.setEnabled(True)

    def _on_apply_token(self):
        description = self.token_page.token_description_edit.text().strip() or "iTrader 智能交易客户端"
        self._on_open_token(description)

    def _on_refresh_token(self):
        self._on_open_token("")

    def _sync_auto_trade_button(self, value: bool):
        self._head_auto_btn.setText("自动交易：开" if value else "自动交易：关")
        self._head_auto_btn.setProperty("variant", "success" if value else "secondary")
        style = self._head_auto_btn.style()
        style.unpolish(self._head_auto_btn)
        style.polish(self._head_auto_btn)

    def _sync_theme_button(self, dark: bool):
        self._head_theme_btn.setText("浅色" if dark else "深色")
        self._head_theme_btn.setChecked(not dark)

    def _toggle_theme(self):
        self._dark = not self._dark
        self.setStyleSheet(qss_for(self._dark))
        if self._vm is not None:
            self._vm.set_theme(self._dark)
        self._sync_theme_button(self._dark)

    def _on_theme_changed(self, dark: bool):
        self._dark = dark
        self.setStyleSheet(qss_for(dark))
        self._sync_theme_button(dark)

    def _append_log(self, text: str, color: str):
        cursor = self.log_page.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text + "\n", fmt)
        self.log_page.log_view.setTextCursor(cursor)
        self.log_page.log_view.ensureCursorVisible()
        self._status_text.setText(text[:60])

    def clear_logs(self):
        self.log_page.log_view.clear()

    def save_approved_token(self, data: dict):
        QMessageBox.information(self, "Token 已保存", "Token 已保存到本地，可启动自动交易。")

    def show_about(self):
        QMessageBox.information(
            self,
            "关于 iTrader 智能交易客户端",
            "iTrader 智能交易客户端\n版本 %s\n\n基于 Clean Architecture + PySide6 构建" % __version__,
        )

    def ask_confirm_quit(self) -> bool:
        return QMessageBox.question(
            self,
            "确认退出",
            "自动交易正在运行，确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes
