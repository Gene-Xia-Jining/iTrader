import json
import sqlite3
from pathlib import Path
from typing import Optional

from ...domain.entities import TradingConfiguration
from ..security.crypto import PasswordCipher, load_or_create_key


class ConfigService:
    """配置持久化到 SQLite（与交易记录共用 data/client.db）。

    使用标准库 sqlite3 同步访问，保持与 Bootstrap.config 同步属性兼容。
    密码字段（tq_password/trade_password）入库前加密，
    load() 返回明文，对消费方透明。
    """

    def __init__(self, db_path: str = "data/client.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        key_path = Path(self.db_path).parent / ".secret.key"
        self._cipher = PasswordCipher(load_or_create_key(key_path))
        self._init_table()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        with self._conn() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS app_config (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    server_url TEXT NOT NULL,
                    symbols TEXT NOT NULL,
                    auto_trade INTEGER NOT NULL,
                    tq_account TEXT NOT NULL,
                    tq_password TEXT NOT NULL,
                    trade_account TEXT NOT NULL DEFAULT '',
                    trade_password TEXT NOT NULL DEFAULT '',
                    initial_balance REAL NOT NULL,
                    database TEXT NOT NULL,
                    CHECK (id = 1)
                )
            """)
            try:
                db.execute("ALTER TABLE app_config ADD COLUMN trade_account TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            try:
                db.execute("ALTER TABLE app_config ADD COLUMN trade_password TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            try:
                db.execute("ALTER TABLE app_config ADD COLUMN proxy_url TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            try:
                db.execute("ALTER TABLE app_config ADD COLUMN auto_check_update INTEGER NOT NULL DEFAULT 1")
            except sqlite3.OperationalError:
                pass
            try:
                db.execute("ALTER TABLE app_config ADD COLUMN skipped_version TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            # 快期账户与模拟账户凭据已合并为 tq_account/tq_password：
            # 先把只在模拟页填过的凭据搬入 tq 列（同密钥，密文直接复制），再删除 sim 列
            try:
                db.execute(
                    "UPDATE app_config SET tq_account = sim_account, tq_password = sim_password"
                    " WHERE id = 1 AND tq_account = '' AND sim_account != ''"
                )
            except sqlite3.OperationalError:
                pass  # 旧库无 sim 列
            for column in ("sim_account", "sim_password"):
                try:
                    db.execute(f"ALTER TABLE app_config DROP COLUMN {column}")
                except sqlite3.OperationalError:
                    pass  # 列已删除或旧 SQLite 不支持 DROP COLUMN（残留无害）
            db.commit()

    def load(self) -> TradingConfiguration:
        with self._conn() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM app_config WHERE id = 1 LIMIT 1").fetchone()
        if row is not None:
            return TradingConfiguration(
                server_url=row["server_url"],
                symbols=json.loads(row["symbols"]),
                auto_trade=bool(row["auto_trade"]),
                tq_account=row["tq_account"],
                tq_password=self._cipher.decrypt(row["tq_password"]),
                initial_balance=row["initial_balance"],
                trade_account=row["trade_account"] if "trade_account" in row.keys() else "",
                trade_password=self._cipher.decrypt(
                    row["trade_password"] if "trade_password" in row.keys() else ""
                ),
                proxy_url=row["proxy_url"] if "proxy_url" in row.keys() else "",
                auto_check_update=bool(row["auto_check_update"]) if "auto_check_update" in row.keys() else True,
                skipped_version=row["skipped_version"] if "skipped_version" in row.keys() else "",
                database_path=row["database"],
            )
        # 首次运行：写入默认配置
        config = TradingConfiguration(
            server_url="http://192.168.100.100:3080",
            symbols=["SA2409"],
            auto_trade=False,
            tq_account="",
            tq_password="",
            initial_balance=10_000_000,
            trade_account="",
            trade_password="",
            proxy_url="",
            auto_check_update=True,
            skipped_version="",
            database_path=self.db_path,
        )
        self.save(config)
        return config

    def save(self, config: TradingConfiguration) -> None:
        with self._conn() as db:
            db.execute("""
                INSERT INTO app_config
                    (id, server_url, symbols, auto_trade, tq_account, tq_password, trade_account, trade_password, proxy_url, auto_check_update, skipped_version, initial_balance, database)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    server_url = excluded.server_url,
                    symbols = excluded.symbols,
                    auto_trade = excluded.auto_trade,
                    tq_account = excluded.tq_account,
                    tq_password = excluded.tq_password,
                    trade_account = excluded.trade_account,
                    trade_password = excluded.trade_password,
                    proxy_url = excluded.proxy_url,
                    auto_check_update = excluded.auto_check_update,
                    skipped_version = excluded.skipped_version,
                    initial_balance = excluded.initial_balance,
                    database = excluded.database
            """, (
                config.server_url,
                json.dumps(config.symbols, ensure_ascii=False),
                int(config.auto_trade),
                config.tq_account,
                self._cipher.encrypt(config.tq_password),
                config.trade_account,
                self._cipher.encrypt(config.trade_password),
                config.proxy_url,
                int(config.auto_check_update),
                config.skipped_version,
                config.initial_balance,
                config.database_path,
            ))
            db.commit()
