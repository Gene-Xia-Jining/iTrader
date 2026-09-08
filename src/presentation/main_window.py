from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..domain.entities import TradingConfiguration
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

        self.server_url_edit = QLineEdit(self._vm.server_url)
        self.server_url_edit.setPlaceholderText("http://localhost:8000")
        form.addRow("服务器地址:", self.server_url_edit)

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

        self.auto_trade_checkbox = QCheckBox("启用自动交易")
        self.auto_trade_checkbox.setChecked(self._vm.auto_trade)
        form.addRow("", self.auto_trade_checkbox)

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
            auto_trade=self.auto_trade_checkbox.isChecked(),
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
        on_start,
        on_stop,
        on_toggle_auto_trade,
        on_open_config,
        on_clear_logs,
        on_show_about,
        on_quit,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._vm = vm
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_toggle_auto_trade = on_toggle_auto_trade
        self._on_open_config = on_open_config
        self._on_clear_logs = on_clear_logs
        self._on_show_about = on_show_about
        self._on_quit = on_quit

        self.setWindowTitle("iTrader 交易客户端")
        self.resize(960, 640)
        self.setMinimumSize(QSize(800, 520))

        self.setStyleSheet(DARK_QSS)

        self._build_menubar()
        self._build_ui()
        self._build_statusbar()
        self._bind_vm()

    # -------- UI --------

    def _build_menubar(self):
        bar: QMenuBar = self.menuBar()

        file_menu = QMenu("文件", self)
        open_config_action = QAction("配置设置...", self)
        open_config_action.setShortcut("Ctrl+,")
        open_config_action.triggered.connect(self._on_open_config)
        file_menu.addAction(open_config_action)
        file_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self._on_quit)
        file_menu.addAction(quit_action)
        bar.addMenu(file_menu)

        trade_menu = QMenu("交易", self)
        start_action = QAction("启动自动交易", self)
        start_action.triggered.connect(self._on_start)
        trade_menu.addAction(start_action)
        stop_action = QAction("停止自动交易", self)
        stop_action.triggered.connect(self._on_stop)
        trade_menu.addAction(stop_action)
        bar.addMenu(trade_menu)

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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal, central)

        # Left control panel
        left = QGroupBox("控制面板", splitter)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 22, 16, 16)
        left_layout.setSpacing(12)

        # Server status row
        server_row = QHBoxLayout()
        server_row.setSpacing(8)
        server_label = QLabel("服务器状态:")
        self.server_status_label = QLabel(self._vm.serverStatus)
        self.server_status_label.setStyleSheet(
            f"color: {self._vm.serverStatusColor}; font-weight: bold;"
        )
        server_row.addWidget(server_label)
        server_row.addWidget(self.server_status_label)
        server_row.addStretch(1)
        left_layout.addLayout(server_row)

        # Trading status row
        trade_row = QHBoxLayout()
        trade_row.setSpacing(8)
        trade_label = QLabel("交易状态:")
        self.trade_status_label = QLabel(self._vm.tradingStatus)
        self.trade_status_label.setStyleSheet(
            f"color: {self._vm.tradingStatusColor}; font-weight: bold;"
        )
        trade_row.addWidget(trade_label)
        trade_row.addWidget(self.trade_status_label)
        trade_row.addStretch(1)
        left_layout.addLayout(trade_row)

        # Control buttons
        self.start_btn = QPushButton("启动自动交易")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setEnabled(self._vm.canStart)
        self.start_btn.clicked.connect(self._on_start)
        left_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止自动交易")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(self._vm.canStop)
        self.stop_btn.clicked.connect(self._on_stop)
        left_layout.addWidget(self.stop_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #45475a;")
        left_layout.addWidget(sep)

        # Auto trade switch
        self.auto_trade_checkbox = QCheckBox("启用自动交易（接收信号后自动下单）")
        self.auto_trade_checkbox.setChecked(self._vm.autoTrade)
        self.auto_trade_checkbox.toggled.connect(self._on_toggle_auto_trade)
        left_layout.addWidget(self.auto_trade_checkbox)

        left_layout.addStretch(1)

        # Config quick button
        config_btn = QPushButton("打开配置...")
        config_btn.setStyleSheet(
            "background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;"
        )
        config_btn.clicked.connect(self._on_open_config)
        left_layout.addWidget(config_btn)

        # Right log panel
        right = QGroupBox("交易日志", splitter)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 22, 16, 16)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "QTextEdit { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 12px; }"
        )
        right_layout.addWidget(self.log_view)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 640])

        layout.addWidget(splitter, 1)

    def _build_statusbar(self):
        bar: QStatusBar = self.statusBar()
        self._status_text = QLabel("就绪")
        self._status_text.setStyleSheet("color: #bac2de; padding-left: 8px;")
        bar.addWidget(self._status_text, 1)

    # -------- VM bindings --------

    def _bind_vm(self):
        self._vm.serverStatusChanged.connect(self._on_server_status_changed)
        self._vm.serverStatusColorChanged.connect(self._on_server_status_color_changed)
        self._vm.tradingStatusChanged.connect(self._on_trade_status_changed)
        self._vm.tradingStatusColorChanged.connect(self._on_trade_status_color_changed)
        self._vm.autoTradeChanged.connect(self._on_auto_trade_changed)
        self._vm.logMessage.connect(self._append_log)
        self._vm.canStartChanged.connect(self._on_can_start_changed)
        self._vm.canStopChanged.connect(self._on_can_stop_changed)

    def _on_server_status_changed(self, value: str):
        self.server_status_label.setText(value)

    def _on_server_status_color_changed(self, color: str):
        self.server_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _on_trade_status_changed(self, value: str):
        self.trade_status_label.setText(value)
        self._status_text.setText(f"交易状态: {value}")

    def _on_trade_status_color_changed(self, color: str):
        self.trade_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _on_auto_trade_changed(self, value: bool):
        if self.auto_trade_checkbox.isChecked() != value:
            self.auto_trade_checkbox.blockSignals(True)
            self.auto_trade_checkbox.setChecked(value)
            self.auto_trade_checkbox.blockSignals(False)

    def _on_can_start_changed(self, value: bool):
        self.start_btn.setEnabled(value)

    def _on_can_stop_changed(self, value: bool):
        self.stop_btn.setEnabled(value)

    def _append_log(self, text: str, color: str):
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text + "\n", fmt)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()
        self._status_text.setText(text[:60])

    # -------- API --------

    def clear_logs(self):
        self.log_view.clear()

    def show_about(self):
        QMessageBox.information(
            self,
            "关于 iTrader",
            f"iTrader 交易客户端\n版本 {__version__}\n\n基于 Clean Architecture + PySide6 构建",
        )

    def ask_confirm_quit(self) -> bool:
        return QMessageBox.question(
            self,
            "确认退出",
            "自动交易正在运行，确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes
