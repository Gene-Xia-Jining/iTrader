from pathlib import Path
from typing import Optional

from ..domain.entities import TradingConfiguration
from ..domain.events import EventBus
from ..domain.repositories import TokenStore, CertificateStore
from ..infrastructure.api.client import (
    FileTokenStore,
    ServerStreamClient,
    TokenApiService,
)
from ..infrastructure.certs.cert_manager import (
    CertificateEnrollmentService,
    FileCertificateStore,
    load_or_generate_client_id,
)
from ..infrastructure.config.config_service import ConfigService
from ..infrastructure.db.repositories import SQLiteTradeCommandRepository
from ..infrastructure.trading.tqsdk_executor import TqSdkTradingExecutor
from .trading_engine import TradingEngine, TradingEngineDeps


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
        self._cert_store: Optional[FileCertificateStore] = None
        self._cert_service: Optional[CertificateEnrollmentService] = None
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

    @property
    def cert_store(self) -> FileCertificateStore:
        if self._cert_store is None:
            self._cert_store = FileCertificateStore()
        return self._cert_store

    @property
    def cert_service(self) -> CertificateEnrollmentService:
        if self._cert_service is None:
            enrollment_url = (
                self.config.enrollment_url
                or self.config.server_url.replace(":3080", ":3081")
            )
            if not enrollment_url.startswith("https"):
                enrollment_url = "https://" + enrollment_url.lstrip("http://").lstrip("https://")
            self._cert_service = CertificateEnrollmentService(
                enrollment_url=enrollment_url,
                store=self.cert_store,
                ca_cert_path=self.config.ca_cert_path or "",
            )
        return self._cert_service

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
                ca_cert_path=self.config.ca_cert_path,
                client_cert_path=self.config.client_cert_path,
                client_key_path=self.config.client_key_path,
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

    def ensure_certs_in_config(self) -> bool:
        cfg = self.config
        if cfg.client_cert_path and Path(cfg.client_cert_path).exists():
            return True
        if self.cert_store.have_cert():
            self._config = TradingConfiguration(
                server_url=cfg.server_url,
                symbols=cfg.symbols,
                auto_trade=cfg.auto_trade,
                tq_account=cfg.tq_account,
                tq_password=cfg.tq_password,
                initial_balance=cfg.initial_balance,
                database_path=cfg.database_path,
                client_cert_path=self.cert_store.client_cert_path(),
                client_key_path=self.cert_store.client_key_path(),
                ca_cert_path=self.cert_store.ca_cert_path(),
                enrollment_url=cfg.enrollment_url,
            )
            return True
        return False
