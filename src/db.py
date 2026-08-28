import time
import aiosqlite


class Database:

    def __init__(self, path: str):
        self.path = path

    async def init(self):

        async with aiosqlite.connect(self.path) as db:

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
                CREATE INDEX IF NOT EXISTS
                idx_trade_commands_symbol
                ON trade_commands(symbol)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_trade_commands_status
                ON trade_commands(status)
            """)

            await db.commit()

    async def exists(self, command_id: str):

        async with aiosqlite.connect(self.path) as db:

            cursor = await db.execute(
                """
                SELECT 1
                FROM trade_commands
                WHERE id = ?
                LIMIT 1
                """,
                (command_id,),
            )

            return await cursor.fetchone() is not None

    async def insert_pending(self, result):

        async with aiosqlite.connect(self.path) as db:

            await db.execute(
                """
                INSERT INTO trade_commands (
                    id,
                    symbol,
                    side,
                    price,
                    target_position,
                    received_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    result.id,
                    result.symbol,
                    result.side,
                    result.price,
                    result.position,
                    result.updated_at,
                ),
            )

            await db.commit()

    async def set_executing(
        self,
        command_id: str,
    ):

        async with aiosqlite.connect(self.path) as db:

            await db.execute(
                """
                UPDATE trade_commands
                SET status = 'executing'
                WHERE id = ?
                """,
                (command_id,),
            )

            await db.commit()

    async def set_executed(
        self,
        command_id: str,
        order_id: str | None = None,
    ):

        async with aiosqlite.connect(self.path) as db:

            await db.execute(
                """
                UPDATE trade_commands
                SET
                    status = 'executed',
                    executed_at = ?,
                    order_id = ?
                WHERE id = ?
                """,
                (
                    int(time.time()),
                    order_id,
                    command_id,
                ),
            )

            await db.commit()

    async def set_failed(
        self,
        command_id: str,
        error: str,
    ):

        async with aiosqlite.connect(self.path) as db:

            await db.execute(
                """
                UPDATE trade_commands
                SET
                    status = 'failed',
                    error = ?
                WHERE id = ?
                """,
                (
                    error,
                    command_id,
                ),
            )

            await db.commit()

    async def set_status(
        self,
        command_id: str,
        status: str,
        error: str | None = None,
    ):

        if status == "executing":
            return await self.set_executing(command_id)
        elif status == "executed":
            return await self.set_executed(command_id)
        elif status == "failed":
            if error is None:
                raise ValueError("错误信息不能为空")
            return await self.set_failed(command_id, error)
        else:
            raise ValueError(f"未知状态: {status}")