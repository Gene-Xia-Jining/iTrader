import asyncio

from tqsdk import (
    TqApi,
    TqSim,
    TqAuth,
    TargetPosTask,
)


class Trader:

    def __init__(
        self,
        account: str,
        password: str,
        initial_balance: float,
    ):

        self.api = TqApi(
            TqSim(
                init_balance=initial_balance
            ),
            auth=TqAuth(
                account,
                password,
            ),
        )

        self.tasks = {}

        self.queue = asyncio.Queue()

    def get_task(self, symbol):

        if symbol not in self.tasks:

            self.tasks[symbol] = (
                TargetPosTask(
                    self.api,
                    symbol,
                    price="ACTIVE",
                )
            )

        return self.tasks[symbol]

    async def execute(
        self,
        symbol: str,
        target_position: int,
    ):

        task = self.get_task(symbol)

        task.set_target_volume(
            target_position
        )

        # 给 TqSdk 一个 update 周期
        await asyncio.to_thread(
            self.api.wait_update
        )

        return True

    async def set_target_position(
        self,
        symbol: str,
        target_position: int,
    ):
        return await self.execute(symbol, target_position)