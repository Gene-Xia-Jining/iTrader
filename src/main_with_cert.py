"""Main entry point with certificate enrollment flow."""
import asyncio
import sys
from pathlib import Path

from config import load_config, save_config, Config
from database import Database
from server import ServerClient
from trader import Trader
from cert_enroll import CertManager


async def ensure_certificates(config: Config) -> bool:
    """Ensure client certificates exist; if not, initiate enrollment."""
    if config.client_cert_path and Path(config.client_cert_path).exists():
        return True

    # fallback: check data/certs
    cert_dir = Path("data/certs")
    if (cert_dir / "client.crt").exists():
        # update config
        config.client_cert_path = str(cert_dir / "client.crt")
        config.client_key_path = str(cert_dir / "client.key")
        config.ca_cert_path = str(cert_dir / "ca.crt")
        return True

    # need enrollment
    enrollment_url = config.enrollment_url or config.server_url.replace(":3080", ":3081")
    if not enrollment_url.startswith("https"):
        enrollment_url = "https://" + enrollment_url
    mgr = CertManager(enrollment_url)

    if mgr.have_cert():
        # already have certs but not in config
        config.client_cert_path = str(mgr.cert_dir / "client.crt")
        config.client_key_path = str(mgr.cert_dir / "client.key")
        config.ca_cert_path = str(mgr.cert_dir / "ca.crt")
        save_config(config)
        return True

    print("=== No client certificate found ===")
    print("Starting enrollment process...")
    contact = input("Contact info (optional): ").strip()
    note = input("Note (optional): ").strip()

    request_id = await mgr.enroll(contact=contact, note=note)
    if not request_id:
        print("Enrollment request failed.")
        return False

    print(f"Enrollment request submitted. Request ID: {request_id}")
    print("Waiting for admin approval... (run `python -m iTrader-Server.admin_cli pending` on server)")

    while True:
        await asyncio.sleep(5)
        status = await mgr.check_status(request_id)
        if status == "approved":
            print("Certificate approved and saved.")
            config.client_cert_path = str(mgr.cert_dir / "client.crt")
            config.client_key_path = str(mgr.cert_dir / "client.key")
            config.ca_cert_path = str(mgr.cert_dir / "ca.crt")
            save_config(config)
            return True
        elif status == "rejected":
            print("Enrollment request rejected.")
            return False
        elif status == "pending":
            print("Still pending...")
        else:
            print("Status check failed.")
            return False


async def main():
    config_dict = load_config()
    config = Config(**config_dict)

    if not await ensure_certificates(config):
        print("Cannot proceed without certificate.")
        sys.exit(1)

    db = Database("data/client.db")
    await db.init()

    trader = Trader(
        account=config.tq_account,
        password=config.tq_password,
        initial_balance=config.initial_balance,
    )

    server = ServerClient(
        server_url=config.server_url,
        symbols=config.symbols,
        ca_cert_path=config.ca_cert_path,
        client_cert_path=config.client_cert_path,
        client_key_path=config.client_key_path,
    )

    while True:
        try:
            async for result in server.stream():
                print("收到策略结果:", result)

                if await db.exists(result.id):
                    print("已经执行过:", result.id)
                    continue

                await db.insert_pending(result)

                if not config.auto_trade:
                    print("自动交易关闭")
                    continue

                try:
                    await db.set_status(result.id, "executing")
                    await trader.set_target_position(
                        result.symbol,
                        result.target_position,
                    )
                    await db.set_status(result.id, "completed")
                except Exception as e:
                    print("交易执行失败:", e)
                    await db.set_status(result.id, "failed", str(e))
        except Exception as e:
            print("连接失败:", e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
