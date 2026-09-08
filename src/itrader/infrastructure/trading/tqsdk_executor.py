import asyncio

from tqsdk import TqApi, TqSim, TqAuth, TargetPosTask

from ...domain.services import TradingExecutor


class TqSdkTradingExecutor(TradingExecutor):
    def __init__(
        self,
        account: str,
        password: str,
        initial_balance: float,
    ):
        self.api = TqApi(
            TqSim(init_balance=initial_balance),
            auth=TqAuth(account, password),
        )
        self.tasks: dict[str, TargetPosTask] = {}

    def _get_task(self, symbol: str) -> TargetPosTask:
        if symbol not in self.tasks:
            self.tasks[symbol] = TargetPosTask(
                self.api,
                symbol,
                price="ACTIVE",
            )
        return self.tasks[symbol]

    async def set_target_position(self, symbol: str, target_position: int) -> None:
        task = self._get_task(symbol)
        task.set_target_volume(target_position)
        await asyncio.to_thread(self.api.wait_update)

    async def close(self) -> None:
        self.api.close()
