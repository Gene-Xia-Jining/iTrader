import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from PySide6.QtWidgets import QApplication

from src.infrastructure.api.client import check_server_health
from src.presentation.main_window import ConfigDialog, MainWindow
from src.presentation.pages import ServerUrlTestRow
from src.presentation.viewmodels import MainViewModel
from src.domain.entities import TradingConfiguration
from src.domain.events import EventBus


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            body = json.dumps({"status": "ok"}).encode()
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


class ServerUrlTestRowTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.row = ServerUrlTestRow()

    def test_empty_url_shows_hint(self):
        self.row.test_btn.click()
        self.assertIn("请先输入服务器地址", self.row.result_label.text())
        self.assertTrue(self.row.test_btn.isEnabled())

    def test_click_invokes_callback_with_url(self):
        calls = []
        self.row.on_test = calls.append
        self.row.url_edit.setText(" http://localhost:8000 ")
        self.row.test_btn.click()
        self.assertEqual(calls, ["http://localhost:8000"])
        self.assertIn("正在测试连接", self.row.result_label.text())
        self.assertFalse(self.row.test_btn.isEnabled())
        self.row.set_result("连接成功", True)
        self.assertTrue(self.row.test_btn.isEnabled())
        self.assertIn("连接成功", self.row.result_label.text())


class CheckServerHealthTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_health_ok(self):
        url = f"http://127.0.0.1:{self.server.server_port}"
        import asyncio

        result = asyncio.run(check_server_health(url))
        self.assertEqual(result["status"], "ok")

    def test_health_failure(self):
        import asyncio

        # 未监听的端口应抛出连接异常
        with self.assertRaises(Exception):
            asyncio.run(check_server_health("http://127.0.0.1:1", timeout=1.0))


class WindowBindingsTest(unittest.TestCase):
    def _make_config(self):
        return TradingConfiguration(
            "http://localhost:8000", ["SHFE.au2510"], True, "acc", "pwd", 1000000
        )

    def test_main_window_binds_settings_test_row(self):
        _make_app()
        calls = []
        window = MainWindow(
            vm=MainViewModel(EventBus(), self._make_config()),
            on_toggle_auto_trade=lambda value: None,
            on_open_config=lambda: None,
            on_open_token=lambda description="": None,
            on_clear_logs=lambda: None,
            on_show_about=lambda: None,
            on_quit=lambda: None,
            on_save_config=lambda data: None,
            on_test_server=calls.append,
        )
        window.settings_page.server_test.url_edit.setText("http://localhost:8000")
        window.settings_page.server_test.test_btn.click()
        self.assertEqual(calls, ["http://localhost:8000"])

    def test_main_window_settings_page_shows_config_values(self):
        _make_app()
        window = MainWindow(
            vm=MainViewModel(EventBus(), self._make_config()),
            on_toggle_auto_trade=lambda value: None,
            on_open_config=lambda: None,
            on_open_token=lambda description="": None,
            on_clear_logs=lambda: None,
            on_show_about=lambda: None,
            on_quit=lambda: None,
            on_save_config=lambda data: None,
            on_test_server=lambda url: None,
        )
        page = window.settings_page
        self.assertEqual(page.server_url_edit.text(), "http://localhost:8000")
        self.assertEqual(page.tq_account_edit.text(), "acc")
        self.assertEqual(page.tq_password_edit.text(), "pwd")
        self.assertEqual(page.balance_edit.text(), "1000000")
        self.assertEqual(page.symbols_edit.text(), "SHFE.au2510")

    def test_config_dialog_test_row(self):
        _make_app()
        calls = []
        dlg = ConfigDialog(None, self._make_config())
        dlg.server_test.on_test = calls.append
        dlg.server_test.url_edit.setText("localhost:8000")
        dlg.server_test.test_btn.click()
        self.assertEqual(calls, ["localhost:8000"])


if __name__ == "__main__":
    unittest.main()
