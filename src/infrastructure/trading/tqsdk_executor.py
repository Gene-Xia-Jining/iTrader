import asyncio

from ...domain.services import TradingExecutor


class TqSdkTradingExecutor(TradingExecutor):
    def __init__(
        self,
        account: str,
        password: str,
        initial_balance: float,
    ):
        self._account = account
        self._password = password
        self._initial_balance = initial_balance
        self._api = None
        self.tasks: dict[str, TargetPosTask] = {}

    @property
    def api(self):
        if self._api is None:
            from tqsdk import TqApi, TqSim, TqAuth
            self._api = TqApi(
                TqSim(init_balance=self._initial_balance),
                auth=TqAuth(self._account, self._password),
            )
        return self._api

    def _get_task(self, symbol: str) -> TargetPosTask:
        if symbol not in self.tasks:
            from tqsdk import TargetPosTask
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
        if self._api is not None:
            self._api.close()
            self._api = None
            self.tasks.clear()
