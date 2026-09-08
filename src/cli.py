import asyncio
import sys
from pathlib import Path

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


async def _ensure_cert(bs: Bootstrap, request_input) -> bool:
    if bs.ensure_certs_in_config():
        return True
    cert_service = bs.cert_service
    if cert_service.have_cert():
        return True
    print("=== 未找到客户端证书 ===")
    print("开始证书注册流程...")
    contact = request_input("联系方式（可选）: ").strip()
    note = request_input("备注（可选）: ").strip()
    request_id = await cert_service.enroll(contact=contact, note=note)
    if not request_id:
        print("证书注册请求失败。")
        return False
    print(f"注册请求已提交，Request ID: {request_id}")
    print("等待管理员批准...")
    while True:
        await asyncio.sleep(5)
        status = await cert_service.check_status(request_id)
        if status == "approved":
            bs.ensure_certs_in_config()
            bs.save_config(bs.config)
            print("证书已批准并保存。")
            return True
        elif status == "rejected":
            print("注册请求被拒绝。")
            return False
        elif status == "pending":
            print("仍在等待批准...")
        else:
            print("状态检查失败。")
            return False


async def run_headless(with_cert: bool = False):
    prepare_workdir()
    bs = Bootstrap()

    if with_cert:
        if not await _ensure_cert(bs, input):
            print("无法在缺少证书的情况下继续运行。")
            sys.exit(1)
    else:
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
    with_cert = "--cert" in sys.argv or "--mtls" in sys.argv
    try:
        asyncio.run(run_headless(with_cert=with_cert))
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
        sys.exit(0)


if __name__ == "__main__":
    main()
