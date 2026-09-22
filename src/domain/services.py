from abc import ABC, abstractmethod

from .entities import StrategySignal


class TradingExecutor(ABC):
    @abstractmethod
    async def set_target_position(self, symbol: str, target_position: int, account_id: str = "") -> None: ...

    @abstractmethod
    async def close(self) -> None: ...


