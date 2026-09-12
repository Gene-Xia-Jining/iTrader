import asyncio
import sys

from .application.bootstrap import Bootstrap
from .application.async_bridge import prepare_workdir
from .domain.events import LogEvent, LogLevel

async def _ensure_token(bs: Bootstrap, request_input) -> bool:
    token_service = bs.token_service
    if token_service.token_store.have_token():
        token = token_service.token_store.load_token()
        if await token_service.validate_token(token):
            return True
        print("⚠️  Token 无效，请求新 token...")
    description = request_input("Enter token description (optional): ").strip()
    token = await token_service.request_new_token(description)
    return bool(token)

async def run_headless():
    prepare_workdir()
    bs = Bootstrap()

    await _ensure_token(bs, input)

    engine = await bs.build_engine()
    engine.set_auto_trade(bs.config.auto_trade)

    def _print_log(evt: LogEvent):
        level_prefix = {
            LogLevel.INFO: "[INFO]",
            LogLevel.WARNING: "[WARN]",
            LogLevel.ERROR: "[ERR ]",
            LogLevel.SUCCESS: "[ OK ]",
        }.get(evt.level, "[LOG]")
        ts = evt.timestamp.strftime("%H:%M:%S")
        print(f"{ts} {level_prefix} {evt.message}")

    bs.event_bus.subscribe(LogEvent, _print_log)

    await engine.start()

def main():
    try:
        asyncio.run(run_headless())
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
        sys.exit(0)

if __name__ == "__main__":
    main()
