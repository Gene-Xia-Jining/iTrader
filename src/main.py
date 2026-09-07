import asyncio
import tomllib

from db import Database
from server import ServerClient
from trader import Trader
from token_manager import TokenManager


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

    # Initialize token manager
    token_manager = TokenManager(config["server_url"])
    
    # Check if we have a valid token
    if not token_manager.have_token():
        print("⚠️  No API token found. Please request a new token.")
        description = input("Enter token description (optional): ").strip()
        await token_manager.request_new_token(description)
    else:
        # Validate existing token
        token = token_manager.load_token()
        if not await token_manager.validate_token(token):
            print("⚠️  Token is invalid or expired. Requesting new token...")
            description = input("Enter token description (optional): ").strip()
            await token_manager.request_new_token(description)
    
    server = ServerClient(
        server_url=config["server_url"],
        symbols=config["symbols"],
        token_manager=token_manager,
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