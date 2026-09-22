import time
from pathlib import Path
from typing import Optional

import aiosqlite

from ...domain.entities import TradeCommand, TradeCommandStatus
from ...domain.repositories import TradeCommandRepository


class SQLiteTradeCommandRepository(TradeCommandRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trade_commands (
                    account_id TEXT NOT NULL DEFAULT '',
                    id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT,
                    price REAL NOT NULL,
                    target_position INTEGER NOT NULL,
                    received_at INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    executed_at INTEGER,
                    order_id TEXT,
                    error TEXT,
                    PRIMARY KEY (account_id, id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_commands_symbol
                ON trade_commands(symbol)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_commands_status
                ON trade_commands(status)
            """)
            await self._migrate_account_id(db)
            await db.commit()

    @staticmethod
    async def _migrate_account_id(db) -> None:
        """把旧版单账户表（id PRIMARY KEY）重建为 (account_id, id) 复合主键。

        SQLite 不支持 ALTER PRIMARY KEY，只能重建表。历史数据回填 account_id=''。
        """
        cursor = await db.execute("PRAGMA table_info(trade_commands)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "account_id" in columns:
            return
        await db.execute("PRAGMA foreign_keys=OFF")
        await db.execute("""
            CREATE TABLE trade_commands_new (
                account_id TEXT NOT NULL DEFAULT '',
                id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT,
                price REAL NOT NULL,
                target_position INTEGER NOT NULL,
                received_at INTEGER NOT NULL,
                status TEXT NOT NULL,
                executed_at INTEGER,
                order_id TEXT,
                error TEXT,
                PRIMARY KEY (account_id, id)
            )
        """)
        await db.execute("""
            INSERT INTO trade_commands_new (
                account_id, id, symbol, side, price, target_position,
                received_at, status, executed_at, order_id, error
            )
            SELECT '', id, symbol, side, price, target_position,
                   received_at, status, executed_at, order_id, error
            FROM trade_commands
        """)
        await db.execute("DROP TABLE trade_commands")
        await db.execute("ALTER TABLE trade_commands_new RENAME TO trade_commands")
        await db.execute("""
            CREATE INDEX idx_trade_commands_symbol
            ON trade_commands(symbol)
        """)
        await db.execute("""
            CREATE INDEX idx_trade_commands_status
            ON trade_commands(status)
        """)
        await db.execute("PRAGMA foreign_keys=ON")

    async def exists(self, account_id: str, command_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM trade_commands WHERE account_id = ? AND id = ? LIMIT 1",
                (account_id, command_id),
            )
            return await cursor.fetchone() is not None

    async def add(self, command: TradeCommand) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO trade_commands (
                    account_id, id, symbol, side, price, target_position, received_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    command.account_id,
                    command.id,
                    command.symbol,
                    command.side,
                    command.price,
                    command.target_position,
                    command.received_at,
                    command.status.value,
                ),
            )
            await db.commit()

    async def get(self, account_id: str, command_id: str) -> Optional[TradeCommand]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM trade_commands WHERE account_id = ? AND id = ? LIMIT 1",
                (account_id, command_id),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return TradeCommand(
                account_id=row["account_id"],
                id=row["id"],
                symbol=row["symbol"],
                side=row["side"],
                price=row["price"],
                target_position=row["target_position"],
                received_at=row["received_at"],
                status=TradeCommandStatus(row["status"]),
                executed_at=row["executed_at"],
                order_id=row["order_id"],
                error=row["error"],
            )

    async def set_status(
        self,
        account_id: str,
        command_id: str,
        status: TradeCommandStatus,
        error: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            if status == TradeCommandStatus.EXECUTING:
                await db.execute(
                    "UPDATE trade_commands SET status = ? WHERE account_id = ? AND id = ?",
                    (status.value, account_id, command_id),
                )
            elif status == TradeCommandStatus.EXECUTED:
                await db.execute(
                    """
                    UPDATE trade_commands
                    SET status = ?, executed_at = ?, order_id = ?
                    WHERE account_id = ? AND id = ?
                    """,
                    (status.value, int(time.time()), order_id, account_id, command_id),
                )
            elif status == TradeCommandStatus.FAILED:
                if error is None:
                    raise ValueError("错误信息不能为空")
                await db.execute(
                    """
                    UPDATE trade_commands
                    SET status = ?, error = ?
                    WHERE account_id = ? AND id = ?
                    """,
                    (status.value, error, account_id, command_id),
                )
            elif status == TradeCommandStatus.PENDING:
                await db.execute(
                    "UPDATE trade_commands SET status = ? WHERE account_id = ? AND id = ?",
                    (status.value, account_id, command_id),
                )
            else:
                raise ValueError(f"未知状态: {status}")
            await db.commit()
