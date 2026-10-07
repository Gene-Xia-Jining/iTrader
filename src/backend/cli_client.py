"""后端测试客户端（验证 RPC 协议，也是 Swift 壳落地前的临时操控入口）。

用法：
  python -m src.backend.cli_client app.status
  python -m src.backend.cli_client config.save '{"server_url":"http://192.168.100.100:3080"}'
  python -m src.backend.cli_client accounts.save '{"kind":"sim","tq_account":"...","tq_password":"..."}'
  python -m src.backend.cli_client --listen 30        # 只监听事件流 30 秒
  python -m src.backend.cli_client                    # 交互 REPL，每行一条：method [params_json]

事件与响应混排打印：响应行前缀 [resp]，事件行前缀 [event]。
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path


def _backend_info() -> dict:
    path = Path("data/backend.json")
    if not path.exists():
        raise SystemExit("未找到 data/backend.json —— 后端未运行？先执行 python -m src.backend")
    return json.loads(path.read_text(encoding="utf-8"))


def _log(prefix: str, payload) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    print(f"{ts} [{prefix}] {text}", flush=True)


class BackendClient:
    def __init__(self, info: dict):
        self._info = info
        self._reader = None
        self._writer = None
        self._next_id = 1

    async def connect(self) -> dict:
        self._reader, self._writer = await asyncio.open_connection(
            "127.0.0.1", self._info["port"], limit=1024 * 1024
        )
        self._send({"v": 1, "token": self._info["token"]})
        hello = json.loads(await asyncio.wait_for(self._reader.readline(), timeout=5))
        if not hello.get("ok"):
            raise SystemExit(f"握手失败: {hello.get('error')}")
        return hello

    def _send(self, payload: dict) -> None:
        self._writer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))

    async def call(self, method: str, params: dict) -> dict:
        """发请求并等待同 id 响应；期间到达的事件实时打印。"""
        req_id = self._next_id
        self._next_id += 1
        self._send({"id": req_id, "method": method, "params": params})
        await self._writer.drain()
        while True:
            line = await self._reader.readline()
            if not line:
                raise SystemExit("连接已断开（后端退出？）")
            msg = json.loads(line)
            if "event" in msg:
                _log(f"event:{msg['event']}", msg.get("data", {}))
                continue
            if msg.get("id") != req_id:
                _log("resp:?", msg)
                continue
            return msg

    async def listen_forever(self) -> None:
        while True:
            line = await self._reader.readline()
            if not line:
                break
            msg = json.loads(line)
            if "event" in msg:
                _log(f"event:{msg['event']}", msg.get("data", {}))

    async def close(self) -> None:
        try:
            self._writer.close()
        except Exception:
            pass


async def _run_oneshot(method: str, params: dict) -> None:
    client = BackendClient(_backend_info())
    hello = await client.connect()
    _log("hello", hello)
    resp = await client.call(method, params)
    _log("resp", resp)
    await client.close()


async def _run_listen(seconds: float) -> None:
    client = BackendClient(_backend_info())
    hello = await client.connect()
    _log("hello", hello)
    print(f"监听事件流 {seconds} 秒，Ctrl+C 退出", flush=True)
    try:
        await asyncio.wait_for(client.listen_forever(), timeout=seconds)
    except asyncio.TimeoutError:
        pass
    await client.close()


async def _run_repl() -> None:
    client = BackendClient(_backend_info())
    hello = await client.connect()
    _log("hello", hello)
    print("输入 method [params_json]，q 退出", flush=True)
    while True:
        try:
            raw = await asyncio.to_thread(input, "> ")
        except (EOFError, KeyboardInterrupt):
            break
        raw = raw.strip()
        if not raw:
            continue
        if raw in ("q", "quit", "exit"):
            break
        parts = raw.split(None, 1)
        method = parts[0]
        try:
            params = json.loads(parts[1]) if len(parts) > 1 else {}
        except json.JSONDecodeError as e:
            print(f"params 不是合法 JSON: {e}", flush=True)
            continue
        resp = await client.call(method, params)
        _log("resp", resp)
    await client.close()


async def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        await _run_repl()
    elif argv[0] == "--listen":
        await _run_listen(float(argv[1]) if len(argv) > 1 else 30.0)
    else:
        method = argv[0]
        try:
            params = json.loads(argv[1]) if len(argv) > 1 else {}
        except json.JSONDecodeError as e:
            raise SystemExit(f"params 不是合法 JSON: {e}")
        await _run_oneshot(method, params)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
