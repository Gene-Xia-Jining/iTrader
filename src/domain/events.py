from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


@dataclass
class LogEvent:
    message: str
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class StatusChangedEvent:
    trading_active: bool
    server_connected: bool


@dataclass
class TradingStartedEvent:
    pass


@dataclass
class TradingStoppedEvent:
    pass


@dataclass
class SignalReceivedEvent:
    signal: Any


@dataclass
class TradeExecutedEvent:
    symbol: str
    target_position: int
    order_id: Optional[str] = None


@dataclass
class TradeFailedEvent:
    symbol: str
    error: str


@dataclass
class ConfigChangedEvent:
    pass


class EventBus:
    def __init__(self):
        self._handlers: dict[type, list] = {}

    def subscribe(self, event_type: type, handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler):
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event):
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception:
                    pass

    async def publish_async(self, event):
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    result = handler(event)
                    if hasattr(result, "__await__"):
                        await result
                except Exception:
                    pass
