from typing import Optional

from PySide6.QtCore import QObject, Signal, Property
from ..domain.entities import TradingConfiguration
from ..domain.events import (
    EventBus,
    LogEvent,
    LogLevel,
    StatusChangedEvent,
    TradingStartedEvent,
    TradingStoppedEvent,
)
from ..domain.events import ConfigChangedEvent
from .theme import log_colors

class MainViewModel(QObject):
    serverStatusChanged = Signal(str)
    serverStatusColorChanged = Signal(str)
    tradingStatusChanged = Signal(str)
    tradingStatusColorChanged = Signal(str)
    autoTradeChanged = Signal(bool)
    logMessage = Signal(str, str)
    configChanged = Signal()
    themeChanged = Signal(bool)

    def __init__(
        self,
        event_bus: EventBus,
        config: TradingConfiguration,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._event_bus = event_bus
        self._config = config
        self._server_connected = False
        # 每个账户独立跟踪运行状态（多引擎可同时运行）
        self._trading_active_by_account: dict[str, bool] = {}
        self._dark = False
        self._log_colors = log_colors(False)
        self._subscribe_events()

    def _subscribe_events(self):
        self._event_bus.subscribe(LogEvent, self._on_log)
        self._event_bus.subscribe(StatusChangedEvent, self._on_status)
        self._event_bus.subscribe(
            TradingStartedEvent, lambda e: self._on_trading_started(e.account_id)
        )
        self._event_bus.subscribe(
            TradingStoppedEvent, lambda e: self._on_trading_stopped(e.account_id)
        )
        self._event_bus.subscribe(ConfigChangedEvent, lambda _e: self.configChanged.emit())

    # ----- Properties -----

    @Property(str, notify=serverStatusChanged)
    def serverStatus(self) -> str:
        return "已连接" if self._server_connected else "未连接"

    @Property(str, notify=serverStatusColorChanged)
    def serverStatusColor(self) -> str:
        return "#2ecc71" if self._server_connected else "#e74c3c"

    @Property(str, notify=tradingStatusChanged)
    def tradingStatus(self) -> str:
        active_accounts = [aid for aid, active in self._trading_active_by_account.items() if active]
        if active_accounts:
            return f"运行中 ({len(active_accounts)})"
        return "已停止"

    @Property(str, notify=tradingStatusColorChanged)
    def tradingStatusColor(self) -> str:
        return "#2ecc71" if self._vm_trading_active() else "#e74c3c"

    def _vm_trading_active(self) -> bool:
        return any(self._trading_active_by_account.values())

    @Property(bool, notify=autoTradeChanged)
    def autoTrade(self) -> bool:
        return self._config.auto_trade

    def setAutoTrade(self, value: bool):
        if self._config.auto_trade != value:
            self._config.auto_trade = value
            self.autoTradeChanged.emit(value)

    @Property(bool, notify=tradingStatusChanged)
    def tradingActive(self) -> bool:
        return self._vm_trading_active()

    @property
    def config(self) -> TradingConfiguration:
        return self._config

    def update_config(self, config: TradingConfiguration) -> None:
        self._config = config
        self.autoTradeChanged.emit(self._config.auto_trade)
        self.configChanged.emit()

    def set_theme(self, dark: bool) -> None:
        """切换明暗主题，更新日志颜色映射并通知 UI。"""
        if self._dark == dark:
            return
        self._dark = dark
        self._log_colors = log_colors(dark)
        self.themeChanged.emit(dark)

    # ----- Event handlers -----

    def _on_log(self, event: LogEvent):
        color = self._log_colors.get(event.level.value, "#ffffff")
        ts = event.timestamp.strftime("%H:%M:%S")
        self.logMessage.emit(f"[{ts}] [{event.level.value}] {event.message}", color)

    def _on_status(self, event: StatusChangedEvent):
        if self._server_connected != event.server_connected:
            self._server_connected = event.server_connected
            self.serverStatusChanged.emit(self.serverStatus)
            self.serverStatusColorChanged.emit(self.serverStatusColor)
        if event.account_id:
            if self._trading_active_by_account.get(event.account_id) != event.trading_active:
                self._trading_active_by_account[event.account_id] = event.trading_active
                self._emit_trading_status()

    def _emit_trading_status(self):
        self.tradingStatusChanged.emit(self.tradingStatus)
        self.tradingStatusColorChanged.emit(self.tradingStatusColor)

    def _on_trading_started(self, account_id: str):
        self._trading_active_by_account[account_id or "legacy"] = True
        self._emit_trading_status()

    def _on_trading_stopped(self, account_id: str):
        self._trading_active_by_account[account_id or "legacy"] = False
        self._emit_trading_status()

class ConfigDialogViewModel(QObject):
    """旧式配置对话框的校验：只处理全局配置（服务器地址）。

    账户凭据与品种已迁到账户表，由交易账号页/模拟交易页维护。
    """

    validated = Signal(dict)
    cancelled = Signal()

    def __init__(self, config: TradingConfiguration, parent=None):
        super().__init__(parent)
        self._config = config

    @property
    def server_url(self) -> str:
        return self._config.server_url

    def submit(
        self,
        server_url: str,
    ) -> tuple[bool, str]:
        if not server_url.strip():
            return False, "服务器地址不能为空"
        result = {
            "server_url": server_url.strip(),
        }
        self.validated.emit(result)
        return True, ""

    def cancel(self):
        self.cancelled.emit()
