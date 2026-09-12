from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class TradeCommandStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"

class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"

@dataclass
class StrategySignal:
    id: str
    symbol: str
    side: Optional[str]
    price: float
    position: int
    updated_at: int

@dataclass
class TradeCommand:
    id: str
    symbol: str
    side: Optional[str]
    price: float
    target_position: int
    received_at: int
    status: TradeCommandStatus = TradeCommandStatus.PENDING
    executed_at: Optional[int] = None
    order_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class TradingConfiguration:
    server_url: str
    symbols: list[str]
    auto_trade: bool
    tq_account: str
    tq_password: str
    initial_balance: float
    database_path: str = "data/client.db"
