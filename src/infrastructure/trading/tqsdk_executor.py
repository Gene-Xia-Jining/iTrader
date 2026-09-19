import asyncio

from ...domain.services import TradingExecutor


class TqSdkTradingExecutor(TradingExecutor):
    def __init__(
        self,
        account: str,
        password: str,
        trade_account: str = "",
        trade_password: str = "",
        broker: str = "",
        initial_balance: float = 10000000.0,
    ):
        self._account = account
        self._password = password
        self._trade_account = trade_account
        self._trade_password = trade_password
        self._broker = broker
        self._initial_balance = initial_balance
        self._api = None
        self.tasks: dict[str, 'TargetPosTask'] = {}

    @property
    def api(self):
        if self._api is None:
            from tqsdk import TqApi, TqSim, TqAccount, TqAuth
            
            if self._broker and self._trade_account and self._trade_password:
                account_obj = TqAccount(self._broker, self._trade_account, self._trade_password)
            else:
                account_obj = TqSim(init_balance=self._initial_balance)
                
            self._api = TqApi(
                account_obj,
                auth=TqAuth(self._account, self._password),
            )
        return self._api

    def _get_task(self, symbol: str) -> 'TargetPosTask':
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
