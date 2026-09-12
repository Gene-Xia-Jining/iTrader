from abc import ABC, abstractmethod
from typing import Optional

from .entities import TradeCommand, TradeCommandStatus

class TradeCommandRepository(ABC):
    @abstractmethod
    async def exists(self, command_id: str) -> bool: ...

    @abstractmethod
    async def add(self, command: TradeCommand) -> None: ...

    @abstractmethod
    async def get(self, command_id: str) -> Optional[TradeCommand]: ...

    @abstractmethod
    async def set_status(
        self,
        command_id: str,
        status: TradeCommandStatus,
        error: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> None: ...

class TokenStore(ABC):
    @abstractmethod
    def have_token(self) -> bool: ...

    @abstractmethod
    def load_token(self) -> Optional[str]: ...

    @abstractmethod
    def save_token(self, token: str) -> None: ...

    @abstractmethod
    def delete_token(self) -> None: ...

class StrategyStreamClient(ABC):
    @abstractmethod
    async def stream(self): ...
