from pathlib import Path
import sys
import tomllib
from typing import Any

from pydantic import BaseModel

from ...domain.entities import TradingConfiguration

class AppConfigModel(BaseModel):
    server_url: str
    symbols: list[str]
    auto_trade: bool = False
    tq_account: str = ""
    tq_password: str = ""
    initial_balance: float = 10_000_000
    database: str = "data/client.db"

class ConfigService:
    def __init__(self, config_path: Path | str = "config.toml"):
        self.config_path = Path(config_path)

    def _resolve_bundled_path(self) -> Path:
        if not self.config_path.exists() and getattr(sys, "frozen", False):
            bundled = Path(sys._MEIPASS) / "config.toml"
            if bundled.exists():
                return bundled
        return self.config_path

    def load(self) -> TradingConfiguration:
        path = self._resolve_bundled_path()
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
            model = AppConfigModel(**data)
            return TradingConfiguration(
                server_url=model.server_url,
                symbols=model.symbols,
                auto_trade=model.auto_trade,
                tq_account=model.tq_account,
                tq_password=model.tq_password,
                initial_balance=model.initial_balance,
                database_path=model.database,
            )
        return TradingConfiguration(
            server_url="http://localhost:8000",
            symbols=["SA2409"],
            auto_trade=False,
            tq_account="",
            tq_password="",
            initial_balance=10_000_000,
            database_path="data/client.db",
        )

    def save(self, config: TradingConfiguration) -> None:
        import toml
        data: dict[str, Any] = {
            "server_url": config.server_url,
            "symbols": config.symbols,
            "auto_trade": config.auto_trade,
            "tq_account": config.tq_account,
            "tq_password": config.tq_password,
            "initial_balance": config.initial_balance,
            "database": config.database_path,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            toml.dump(data, f)
