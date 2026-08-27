import asyncio
import tomllib

from .database import Database
from .server import ServerClient
from .trader import Trader


async def main():

    with open(
        "config.toml",
        "rb",
    ) as f:

        config = tomllib.load(f)

    db = Database(
        "data/client.db"
    )

    await db.init()

    trader = Trader(
        account=config["tq_account"],
        password=config["tq_password"],
        initial_balance=config["initial_balance"],
    )

    server = ServerClient(
        server_url=config["server_url"],
        symbols=config["symbols"],
    )

    while True:

        try:

            async for result in server.stream():

                print(
                    "收到策略结果:",
                    result,
                )

                # 幂等检查
                if await db.exists(result.id):

                    print(
                        "已经执行过:",
                        result.id,
                    )

                    continue

                # 先落库
                await db.insert_pending(result)

                # 自动交易关闭
                if not config["auto_trade"]:

                    print(
                        "自动交易关闭"
                    )

                    continue

                try:

                    await db.set_status(
                        result.id,
                        "executing",
                    )

                    await trader.set_target_position(
                        result.symbol,
                        result.position,
                    )

                    await db.set_status(
                        result.id,
                        "executed",
                    )

                    print(
                        "交易执行成功:",
                        result.symbol,
                        result.position,
                    )

                except Exception as e:

                    await db.set_status(
                        result.id,
                        "failed",
                        error=str(e),
                    )

                    print(
                        "交易执行失败:",
                        e,
                    )

        except Exception as e:

            print(
                "服务器连接断开:",
                e,
            )

            await asyncio.sleep(5)


if __name__ == "__main__":

    asyncio.run(main())