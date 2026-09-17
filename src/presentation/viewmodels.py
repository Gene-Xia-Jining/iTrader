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
        self._trading_active = False
        self._dark = False
        self._log_colors = log_colors(False)
        self._subscribe_events()

    def _subscribe_events(self):
        self._event_bus.subscribe(LogEvent, self._on_log)
        self._event_bus.subscribe(StatusChangedEvent, self._on_status)
        self._event_bus.subscribe(TradingStartedEvent, lambda _e: self._on_trading_started())
        self._event_bus.subscribe(TradingStoppedEvent, lambda _e: self._on_trading_stopped())
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
        return "运行中" if self._trading_active else "已停止"

    @Property(str, notify=tradingStatusColorChanged)
    def tradingStatusColor(self) -> str:
        return "#2ecc71" if self._trading_active else "#e74c3c"

    @Property(bool, notify=autoTradeChanged)
    def autoTrade(self) -> bool:
        return self._config.auto_trade

    def setAutoTrade(self, value: bool):
        if self._config.auto_trade != value:
            self._config.auto_trade = value
            self.autoTradeChanged.emit(value)

    @Property(bool, notify=tradingStatusChanged)
    def tradingActive(self) -> bool:
        return self._trading_active

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
        if self._trading_active != event.trading_active:
            self._trading_active = event.trading_active
            self.tradingStatusChanged.emit(self.tradingStatus)
            self.tradingStatusColorChanged.emit(self.tradingStatusColor)

    def _on_trading_started(self):
        if not self._trading_active:
            self._trading_active = True
            self.tradingStatusChanged.emit(self.tradingStatus)
            self.tradingStatusColorChanged.emit(self.tradingStatusColor)

    def _on_trading_stopped(self):
        if self._trading_active:
            self._trading_active = False
            self.tradingStatusChanged.emit(self.tradingStatus)
            self.tradingStatusColorChanged.emit(self.tradingStatusColor)

class ConfigDialogViewModel(QObject):
    validated = Signal(dict)
    cancelled = Signal()

    def __init__(self, config: TradingConfiguration, parent=None):
        super().__init__(parent)
        self._config = config

    @property
    def server_url(self) -> str:
        return self._config.server_url

    @property
    def tq_account(self) -> str:
        return self._config.tq_account

    @property
    def tq_password(self) -> str:
        return self._config.tq_password

    @property
    def initial_balance(self) -> float:
        return self._config.initial_balance

    @property
    def symbols(self) -> list[str]:
        return list(self._config.symbols)

    def symbols_text(self) -> str:
        return ",".join(self._config.symbols)

    def submit(
        self,
        server_url: str,
        tq_account: str,
        tq_password: str,
        initial_balance_str: str,
        symbols_str: str,
    ) -> tuple[bool, str]:
        try:
            initial_balance = float(initial_balance_str)
        except ValueError:
            return False, "初始资金必须是数字"
        symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
        if not symbols:
            return False, "至少需要一个交易品种"
        if not server_url.strip():
            return False, "服务器地址不能为空"
        result = {
            "server_url": server_url.strip(),
            "tq_account": tq_account,
            "tq_password": tq_password,
            "initial_balance": initial_balance,
            "symbols": symbols,
        }
        self.validated.emit(result)
        return True, ""

    def cancel(self):
        self.cancelled.emit()
