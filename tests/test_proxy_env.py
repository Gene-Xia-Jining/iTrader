import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLineEdit

from src.infrastructure.config.config_service import ConfigService
from src.infrastructure.proxy import SYSTEM_PROXY, apply_proxy_environment, server_host
from src.presentation.pages import SettingsPage
from tests.test_simulation_page import _make_config

_PROXY_ENV_KEYS = ("NO_PROXY", "no_proxy", "WSS_PROXY", "wss_proxy")


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


class ProxyEnvTest(unittest.TestCase):
    def setUp(self):
        # 备份相关环境变量，避免污染进程状态
        self._backup = {k: os.environ.get(k) for k in _PROXY_ENV_KEYS}

    def tearDown(self):
        for k, v in self._backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_empty_proxy_forces_direct(self):
        os.environ["WSS_PROXY"] = "socks5://127.0.0.1:1080"
        apply_proxy_environment("", ["192.168.100.100"])
        self.assertEqual(os.environ["NO_PROXY"], "*")
        self.assertEqual(os.environ["no_proxy"], "*")
        self.assertNotIn("WSS_PROXY", os.environ)

    def test_proxy_sets_wss_and_bypass(self):
        apply_proxy_environment("http://127.0.0.1:7890", ["192.168.100.100"])
        self.assertEqual(os.environ["WSS_PROXY"], "http://127.0.0.1:7890")
        self.assertEqual(os.environ["wss_proxy"], "http://127.0.0.1:7890")
        self.assertEqual(os.environ["NO_PROXY"], "192.168.100.100")
        self.assertEqual(os.environ["no_proxy"], "192.168.100.100")

    def test_system_proxy_clears_overrides(self):
        os.environ["NO_PROXY"] = "*"
        os.environ["WSS_PROXY"] = "http://127.0.0.1:7890"
        apply_proxy_environment(SYSTEM_PROXY, ["192.168.100.100"])
        for key in _PROXY_ENV_KEYS:
            self.assertNotIn(key, os.environ)

    def test_server_host_extraction(self):
        self.assertEqual(server_host("http://192.168.100.100:3080"), "192.168.100.100")
        self.assertEqual(server_host("192.168.100.100:3080"), "192.168.100.100")
        self.assertEqual(server_host("  http://my-server.local/  "), "my-server.local")


class ConfigServiceProxyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "client.db"
        self.service = ConfigService(str(self.db_path))

    def tearDown(self):
        self._tmp.cleanup()

    def test_proxy_url_roundtrip_and_migration(self):
        self.service.save(_make_config(proxy_url="http://127.0.0.1:7890", database_path=str(self.db_path)))
        self.assertEqual(self.service.load().proxy_url, "http://127.0.0.1:7890")
        # 旧库（无 proxy_url 列）迁移后可读取
        conn = sqlite3.connect(self.db_path)
        conn.execute("ALTER TABLE app_config RENAME TO app_config_old")
        conn.execute("""
            CREATE TABLE app_config (
                id INTEGER PRIMARY KEY DEFAULT 1,
                server_url TEXT NOT NULL,
                symbols TEXT NOT NULL,
                auto_trade INTEGER NOT NULL,
                tq_account TEXT NOT NULL,
                tq_password TEXT NOT NULL,
                trade_account TEXT NOT NULL DEFAULT '',
                trade_password TEXT NOT NULL DEFAULT '',
                sim_account TEXT NOT NULL DEFAULT '',
                sim_password TEXT NOT NULL DEFAULT '',
                initial_balance REAL NOT NULL,
                database TEXT NOT NULL,
                CHECK (id = 1)
            )
        """)
        conn.execute(
            "INSERT INTO app_config (id, server_url, symbols, auto_trade, tq_account, tq_password, initial_balance, database)"
            " SELECT id, server_url, symbols, auto_trade, tq_account, tq_password, initial_balance, database FROM app_config_old"
        )
        conn.execute("DROP TABLE app_config_old")
        conn.commit()
        conn.close()
        self.assertEqual(ConfigService(str(self.db_path)).load().proxy_url, "")


class SettingsPageProxyTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.page = SettingsPage()

    def test_set_config_fills_proxy(self):
        self.page.set_config(_make_config(proxy_url="http://127.0.0.1:7890"))
        self.assertTrue(self.page.proxy_custom_radio.isChecked())
        self.assertTrue(self.page.proxy_edit.isEnabled())
        self.assertEqual(self.page.proxy_edit.text(), "http://127.0.0.1:7890")

    def test_set_config_system_and_direct(self):
        self.page.set_config(_make_config(proxy_url=SYSTEM_PROXY))
        self.assertTrue(self.page.proxy_system_radio.isChecked())
        self.assertFalse(self.page.proxy_edit.isEnabled())
        self.page.set_config(_make_config())
        self.assertTrue(self.page.proxy_direct_radio.isChecked())
        self.assertEqual(self.page._current_proxy_value(), "")

    def test_save_includes_proxy(self):
        self.page.set_config(_make_config(proxy_url="http://127.0.0.1:7890"))
        self.page.server_url_edit.setText("http://192.168.100.100:3080")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured.get("proxy_url"), "http://127.0.0.1:7890")
        self.assertEqual(captured.get("server_url"), "http://192.168.100.100:3080")

    def test_save_system_proxy(self):
        self.page.server_url_edit.setText("http://192.168.100.100:3080")
        self.page.proxy_system_radio.setChecked(True)
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured.get("proxy_url"), SYSTEM_PROXY)


if __name__ == "__main__":
    unittest.main()
