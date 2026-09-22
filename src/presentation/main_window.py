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
    QProgressDialog,
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
from .pages import AccountPage, DashboardPage, make_button, LogPage, ServerUrlTestRow, SettingsPage, SimulationPage, TokenPage
from .theme import qss_for, status_color
from .viewmodels import ConfigDialogViewModel, MainViewModel


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

        hint = QLabel("交易账户在「实盘交易」页维护，模拟账户在「模拟交易」页维护。")
        hint.setObjectName("dim")
        form.addRow("", hint)

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
        on_save_simulation=None,
        on_test_simulation=None,
        on_test_server=None,
        on_fetch_symbols=None,
        on_check_update=None,
        on_cancel_update=None,
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
        self._on_save_simulation = on_save_simulation
        self._on_test_simulation = on_test_simulation
        self._on_test_server = on_test_server
        self._on_fetch_symbols = on_fetch_symbols
        self._on_check_update = on_check_update
        self._on_cancel_update = on_cancel_update
        self._update_progress_dlg = None

        self.setWindowTitle("iTrader 智能交易系统")
        self.resize(1180, 760)
        self.setMinimumSize(QSize(960, 620))
        self._dark = False
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
        check_update_action = QAction("检查更新...", self)
        check_update_action.triggered.connect(self.start_check_update)
        help_menu.addAction(check_update_action)
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
        brand_label = QLabel("iTrader 智能交易系统", head)
        brand_label.setObjectName("title")
        head_layout.addWidget(brand_label)
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
        self.simulation_btn = SidebarButton("模拟交易", sidebar)
        self.account_btn = SidebarButton("实盘交易", sidebar)
        self.settings_btn = SidebarButton("设置", sidebar)
        for button in (
            self.dashboard_btn,
            self.token_btn,
            self.log_btn,
            self.simulation_btn,
            self.account_btn,
            self.settings_btn,
        ):
            nav.addWidget(button)
        self.dashboard_btn.setChecked(True)
        self.dashboard_btn.clicked.connect(lambda: self._switch_page(0))
        self.token_btn.clicked.connect(lambda: self._switch_page(1))
        self.log_btn.clicked.connect(lambda: self._switch_page(2))
        self.simulation_btn.clicked.connect(lambda: self._switch_page(3))
        self.account_btn.clicked.connect(lambda: self._switch_page(4))
        self.settings_btn.clicked.connect(lambda: self._switch_page(5))
        sidebar_layout.addLayout(nav)
        sidebar_layout.addStretch(1)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.token_page = TokenPage()
        self.log_page = LogPage()
        self.simulation_page = SimulationPage()
        self.account_page = AccountPage()
        self.settings_page = SettingsPage()
        # Connect settings page save callback（设置页只保留服务器/代理/更新）
        self.settings_page.on_save = self._on_save_config
        self.settings_page.server_test.on_test = self._on_test_server
        self.settings_page.on_check_update = self._on_check_update
        self.settings_page.set_config(self._vm.config)
        # Connect account page save callback
        self.account_page.on_save = self._on_save_account
        # Connect simulation page save callback
        self.simulation_page.on_save = self._on_save_simulation
        self.simulation_page.on_test = self._on_test_simulation
        self.simulation_page.on_fetch_symbols = self._on_fetch_symbols
        for page in (
            self.dashboard_page,
            self.token_page,
            self.log_page,
            self.simulation_page,
            self.account_page,
            self.settings_page,
        ):
            self.stack.addWidget(page)
        self.stack.setCurrentIndex(0)

        self.dashboard_page.config_btn.clicked.connect(lambda: self._switch_page(5))
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
        self.simulation_btn.setChecked(index == 3)
        self.account_btn.setChecked(index == 4)
        self.settings_btn.setChecked(index == 5)
        if index in (3, 4) and self._on_fetch_symbols:
            self._on_fetch_symbols()

    def _build_statusbar(self):
        bar = self.statusBar()
        self._status_text = QLabel("就绪")
        bar.addWidget(self._status_text, 1)

        indicators = QWidget()
        indicators_layout = QHBoxLayout(indicators)
        indicators_layout.setContentsMargins(0, 0, 10, 0)
        indicators_layout.setSpacing(6)
        self._server_dot = QLabel(indicators)
        self._server_dot.setFixedSize(6, 6)
        self._server_label = QLabel("服务器: 未连接", indicators)
        self._server_label.setObjectName("dim")
        self._trade_dot = QLabel(indicators)
        self._trade_dot.setFixedSize(6, 6)
        self._trade_label = QLabel("交易: 已停止", indicators)
        self._trade_label.setObjectName("dim")
        indicators_layout.addWidget(self._server_dot)
        indicators_layout.addWidget(self._server_label)
        indicators_layout.addSpacing(12)
        indicators_layout.addWidget(self._trade_dot)
        indicators_layout.addWidget(self._trade_label)
        bar.addPermanentWidget(indicators)
        self._sync_status_indicators()

    def _sync_status_indicators(self):
        """状态栏右侧的服务器/交易状态指示器与 ViewModel 保持一致。"""
        self._server_dot.setStyleSheet(
            "background-color: %s; border-radius: 3px; border: 0;" % self._vm.serverStatusColor
        )
        self._server_label.setText(f"服务器: {self._vm.serverStatus}")
        self._trade_dot.setStyleSheet(
            "background-color: %s; border-radius: 3px; border: 0;" % self._vm.tradingStatusColor
        )
        self._trade_label.setText(f"交易: {self._vm.tradingStatus}")

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
        self._vm.configChanged.connect(self._refresh_dashboard_metrics)
        self._on_server_status_changed(self._vm.serverStatus)
        self._on_server_status_color_changed(self._vm.serverStatusColor)
        self._on_trade_status_changed(self._vm.tradingStatus)
        self._on_trade_status_color_changed(self._vm.tradingStatusColor)
        self._refresh_dashboard_metrics()

    def _on_server_status_changed(self, value: str):
        self.dashboard_page.server_status.set_status(value, self._vm.serverStatusColor)
        self._sync_status_indicators()

    def _on_server_status_color_changed(self, color: str):
        self.dashboard_page.server_status.set_status(self._vm.serverStatus, color)

    def _on_trade_status_changed(self, value: str):
        self.dashboard_page.trade_status.set_status(value, self._vm.tradingStatusColor)
        self._sync_status_indicators()
        self._sync_trade_caption()
        self._status_text.setText(f"交易状态: {value}")
        self._sync_auto_trade_button(self._vm.tradingActive)

    def _refresh_dashboard_metrics(self):
        """配置变化时同步仪表盘的服务器地址说明。账户资金与活跃品种由账户同步驱动。"""
        config = self._vm.config
        self.dashboard_page.server_status.set_secondary(config.server_url or "未配置服务器地址")

    def sync_accounts_to_dashboard(self, accounts: list):
        """用账户列表刷新仪表盘统计：活跃品种数与账户数。"""
        all_symbols = set()
        for a in accounts:
            if a.enabled:
                all_symbols.update(a.symbols)
        live_count = sum(1 for a in accounts if a.kind == "live" and a.enabled)
        sim_count = sum(1 for a in accounts if a.kind == "sim" and a.enabled)
        # 初始资金不再为配置项，显示启用账户概况
        self.dashboard_page.balance_card.set_value(f"{live_count} 实盘 / {sim_count} 模拟")
        self.dashboard_page.symbols_card.set_value(str(len(all_symbols)))

    def _sync_trade_caption(self):
        self.dashboard_page.trade_status.set_secondary(
            "自动交易运行中" if self._vm.tradingActive else "自动交易未启动"
        )

    def _on_trade_status_color_changed(self, color: str):
        self.dashboard_page.trade_status.set_status(self._vm.tradingStatus, color)

    def set_token_status(self, text: str):
        self.token_page.token_status_label.setText(text)
        self.token_page.token_status_label.setStyleSheet(
            f"color: {status_color(text)}; background: transparent;"
        )
        if "已通过" in text:
            self.token_page.token_status_btn.setEnabled(True)

    def _on_apply_token(self):
        description = self.token_page.token_description_edit.text().strip() or "iTrader 智能交易系统"
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
        preview = self.dashboard_page.log_preview
        preview_cursor = preview.textCursor()
        preview_cursor.movePosition(QTextCursor.End)
        # 换行前置而非尾部追加，避免空尾块占用 maximumBlockCount 配额
        prefix = "\n" if preview_cursor.position() > 0 else ""
        preview_cursor.insertText(prefix + text, QTextCharFormat(fmt))
        preview.setTextCursor(preview_cursor)
        preview.ensureCursorVisible()
        self._status_text.setText(text[:60])

    def clear_logs(self):
        self.log_page.log_view.clear()
        self.dashboard_page.log_preview.clear()

    def save_approved_token(self, data: dict):
        QMessageBox.information(self, "Token 已保存", "Token 已保存到本地，可启动自动交易。")

    def show_server_not_connected(self):
        QMessageBox.warning(self, "自动交易", "服务器未连接")

    def show_about(self):
        QMessageBox.information(
            self,
            "关于 iTrader 智能交易系统",
            "iTrader 智能交易系统\n版本 %s\n\n基于 Clean Architecture + PySide6 构建" % __version__,
        )

    # -------- 自动更新 --------

    def start_check_update(self):
        """检查更新统一入口（帮助菜单/设置页），结果回显在设置页状态区。"""
        self.settings_page.start_check_update()

    def show_update_available(self, release) -> str:
        """发现新版本对话框，返回用户选择：update / skip / page / later。"""
        notes = (release.notes or "").strip()
        if len(notes) > 600:
            notes = notes[:600] + "…"
        box = QMessageBox(self)
        box.setWindowTitle("发现新版本")
        box.setText(f"发现新版本 v{release.version}，当前版本 v{__version__}")
        if notes:
            box.setInformativeText(notes)
        update_btn = box.addButton("立即更新", QMessageBox.AcceptRole)
        page_btn = box.addButton("打开下载页", QMessageBox.ActionRole)
        skip_btn = box.addButton("跳过此版本", QMessageBox.ActionRole)
        box.addButton("稍后", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is update_btn:
            return "update"
        if clicked is skip_btn:
            return "skip"
        if clicked is page_btn:
            return "page"
        return "later"

    def begin_update_progress(self):
        """创建下载进度对话框（模态，可取消，取消经回调转发给控制器）。"""
        dlg = QProgressDialog("正在下载更新…", "取消", 0, 100, self)
        dlg.setWindowTitle("正在更新 iTrader")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setMinimumWidth(380)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.canceled.connect(self._on_update_cancel_clicked)
        self._update_progress_dlg = dlg
        dlg.show()

    def set_update_progress(self, pct: int, received: int, total: int):
        dlg = self._update_progress_dlg
        if dlg is None:
            return
        if total > 0:
            dlg.setLabelText(
                f"正在下载更新… {received / 1048576:.1f} / {total / 1048576:.1f} MB"
            )
        else:
            dlg.setLabelText(f"正在下载更新… 已下载 {received / 1048576:.1f} MB")
        if pct >= 0:
            dlg.setValue(pct)

    def finish_update_progress(self):
        """关闭下载进度对话框（完成/失败/取消时调用，不触发取消信号）。"""
        dlg = self._update_progress_dlg
        self._update_progress_dlg = None
        if dlg is not None:
            dlg.reset()
            dlg.deleteLater()

    def _on_update_cancel_clicked(self):
        if self._on_cancel_update is not None:
            self._on_cancel_update()

    def show_update_ready(self, kind_label: str) -> bool:
        return QMessageBox.question(
            self,
            "更新已就绪",
            f"{kind_label}已下载完成，将退出应用并完成安装。\n是否立即重启？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        ) == QMessageBox.Yes

    def show_update_error(self, message: str):
        QMessageBox.warning(self, "更新失败", message)

    def ask_confirm_quit(self) -> bool:
        return QMessageBox.question(
            self,
            "确认退出",
            "自动交易正在运行，确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes
