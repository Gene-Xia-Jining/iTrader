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
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT,
                    price REAL NOT NULL,
                    target_position INTEGER NOT NULL,
                    received_at INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    executed_at INTEGER,
                    order_id TEXT,
                    error TEXT
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
            await db.commit()

    async def exists(self, command_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM trade_commands WHERE id = ? LIMIT 1",
                (command_id,),
            )
            return await cursor.fetchone() is not None

    async def add(self, command: TradeCommand) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO trade_commands (
                    id, symbol, side, price, target_position, received_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
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

    async def get(self, command_id: str) -> Optional[TradeCommand]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM trade_commands WHERE id = ? LIMIT 1",
                (command_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return TradeCommand(
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
        command_id: str,
        status: TradeCommandStatus,
        error: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            if status == TradeCommandStatus.EXECUTING:
                await db.execute(
                    "UPDATE trade_commands SET status = ? WHERE id = ?",
                    (status.value, command_id),
                )
            elif status == TradeCommandStatus.EXECUTED:
                await db.execute(
                    """
                    UPDATE trade_commands
                    SET status = ?, executed_at = ?, order_id = ?
                    WHERE id = ?
                    """,
                    (status.value, int(time.time()), order_id, command_id),
                )
            elif status == TradeCommandStatus.FAILED:
                if error is None:
                    raise ValueError("错误信息不能为空")
                await db.execute(
                    """
                    UPDATE trade_commands
                    SET status = ?, error = ?
                    WHERE id = ?
                    """,
                    (status.value, error, command_id),
                )
            elif status == TradeCommandStatus.PENDING:
                await db.execute(
                    "UPDATE trade_commands SET status = ? WHERE id = ?",
                    (status.value, command_id),
                )
            else:
                raise ValueError(f"未知状态: {status}")
            await db.commit()
