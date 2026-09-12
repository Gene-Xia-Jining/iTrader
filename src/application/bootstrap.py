import uuid
from pathlib import Path
from typing import Optional

from ..domain.entities import TradingConfiguration
from ..domain.events import EventBus
from ..infrastructure.api.client import (
    FileTokenStore,
    ServerStreamClient,
    TokenApiService,
)
from ..infrastructure.config.config_service import ConfigService
from ..infrastructure.db.repositories import SQLiteTradeCommandRepository
from ..infrastructure.trading.tqsdk_executor import TqSdkTradingExecutor
from .trading_engine import TradingEngine, TradingEngineDeps

def load_or_generate_client_id() -> str:
    id_path = Path("data/client_id.txt")
    if id_path.exists():
        return id_path.read_text(encoding="utf-8").strip()
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    id_path.parent.mkdir(parents=True, exist_ok=True)
    id_path.write_text(client_id, encoding="utf-8")
    return client_id

class Bootstrap:
    def __init__(
        self,
        config_path: str | Path = "config.toml",
    ):
        self.config_service = ConfigService(config_path)
        self.event_bus = EventBus()
        self._config: Optional[TradingConfiguration] = None
        self._trade_repo: Optional[SQLiteTradeCommandRepository] = None
        self._trading_executor: Optional[TqSdkTradingExecutor] = None
        self._stream_client: Optional[ServerStreamClient] = None
        self._token_store: Optional[FileTokenStore] = None
        self._token_service: Optional[TokenApiService] = None
        self._engine: Optional[TradingEngine] = None

    @property
    def config(self) -> TradingConfiguration:
        if self._config is None:
            self._config = self.config_service.load()
        return self._config

    def save_config(self, config: TradingConfiguration) -> None:
        self._config = config
        self.config_service.save(config)

    @property
    def token_store(self) -> FileTokenStore:
        if self._token_store is None:
            self._token_store = FileTokenStore()
        return self._token_store

    @property
    def token_service(self) -> TokenApiService:
        if self._token_service is None:
            self._token_service = TokenApiService(
                server_url=self.config.server_url,
                token_store=self.token_store,
                client_id=load_or_generate_client_id(),
            )
        return self._token_service

    async def init_db(self) -> SQLiteTradeCommandRepository:
        if self._trade_repo is None:
            self._trade_repo = SQLiteTradeCommandRepository(self.config.database_path)
            await self._trade_repo.init()
        return self._trade_repo

    def build_trading_executor(self) -> TqSdkTradingExecutor:
        if self._trading_executor is None:
            self._trading_executor = TqSdkTradingExecutor(
                account=self.config.tq_account,
                password=self.config.tq_password,
                initial_balance=self.config.initial_balance,
            )
        return self._trading_executor

    def build_stream_client(self) -> ServerStreamClient:
        if self._stream_client is None:
            self._stream_client = ServerStreamClient(
                server_url=self.config.server_url,
                symbols=self.config.symbols,
                token_service=self.token_service,
            )
        return self._stream_client

    async def build_engine(self) -> TradingEngine:
        if self._engine is None:
            trade_repo = await self.init_db()
            self._engine = TradingEngine(
                deps=TradingEngineDeps(
                    config=self.config,
                    trade_repo=trade_repo,
                    stream_client=self.build_stream_client(),
                    trading_executor=self.build_trading_executor(),
                    event_bus=self.event_bus,
                    auto_trade=self.config.auto_trade,
                )
            )
        return self._engine

    def reset_engine(self) -> None:
        self._engine = None
        self._trading_executor = None
        self._stream_client = None
