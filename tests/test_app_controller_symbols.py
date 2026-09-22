"""控制器侧品种拉取链路：handle_fetch_symbols 无参、地址取自配置、失败上报。"""

import asyncio
import inspect
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from src.domain.entities import TradingConfiguration
from src.presentation.app_controller import AppController

SERVER_SYMBOLS = ["IF", "IH", "IC"]


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


def _config(server_url: str) -> TradingConfiguration:
    return TradingConfiguration(
        server_url=server_url, auto_trade=False, database_path="data/client.db"
    )


class _SymbolHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/symbols":
            body = json.dumps({"symbols": SERVER_SYMBOLS}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class _SymbolServerTestBase(unittest.TestCase):
    """每个用例一套临时数据目录 + 信号收集。"""

    def setUp(self):
        _make_app()
        self._tmp = tempfile.TemporaryDirectory()
        self.ctrl = AppController(QApplication.instance(), Path(self._tmp.name))
        self.emitted = []
        self.ctrl.symbols_fetched.connect(self._collect)

    def tearDown(self):
        self._tmp.cleanup()

    def _collect(self, success, message, symbols):
        self.emitted.append((success, message, symbols))

    def _start_server(self):
        server = HTTPServer(("127.0.0.1", 0), _SymbolHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return f"http://127.0.0.1:{server.server_address[1]}"


class FetchSymbolsTest(_SymbolServerTestBase):
    def test_fetch_symbols_uses_configured_server_url(self):
        # 端到端：请求打到 config.server_url，结果原样上报
        url = self._start_server()
        self.ctrl.bootstrap.save_config(_config(url))
        asyncio.run(self.ctrl._fetch_symbols())
        self.assertEqual(self.emitted, [(True, "获取成功，共 3 个品种", SERVER_SYMBOLS)])

    def test_fetch_symbols_empty_url_skips_network(self):
        self.ctrl.bootstrap.save_config(_config(""))
        with patch("src.presentation.app_controller.fetch_server_symbols") as fake:
            asyncio.run(self.ctrl._fetch_symbols())
        fake.assert_not_called()
        self.assertEqual(self.emitted, [(False, "未配置服务器地址", [])])

    def test_fetch_symbols_emits_failure_on_error(self):
        self.ctrl.bootstrap.save_config(_config("http://127.0.0.1:1"))
        with patch(
            "src.presentation.app_controller.fetch_server_symbols",
            side_effect=ConnectionError("拒绝连接"),
        ):
            asyncio.run(self.ctrl._fetch_symbols())
        self.assertEqual(self.emitted, [(False, "获取失败: 拒绝连接", [])])


class HandleFetchSymbolsTest(_SymbolServerTestBase):
    def test_handle_fetch_symbols_accepts_no_arguments(self):
        # 回归：切页与刷新按钮都调用 handle_fetch_symbols()，不传 server_url
        self.ctrl.bootstrap.save_config(_config(""))
        self.assertEqual(str(inspect.signature(AppController._fetch_symbols)), "(self)")
        with patch.object(self.ctrl, "_run_async") as run_async:
            self.ctrl.handle_fetch_symbols()
        self.assertEqual(run_async.call_count, 1)
        coro = run_async.call_args.args[0]
        self.assertTrue(asyncio.iscoroutine(coro))

        # 驱动实际协程，确认无参 _fetch_symbols() 跑完且不发网络请求
        with patch("src.presentation.app_controller.fetch_server_symbols") as fake:
            asyncio.run(coro)
        fake.assert_not_called()
        self.assertEqual(self.emitted, [(False, "未配置服务器地址", [])])


if __name__ == "__main__":
    unittest.main()
