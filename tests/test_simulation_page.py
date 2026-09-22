import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit

from src.domain.entities import Account, TradingConfiguration
from src.infrastructure.config.config_service import ConfigService
from src.presentation.pages import SimulationPage


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


def _make_account(**overrides):
    fields = dict(
        id="legacy",
        kind="sim",
        label="模拟账户",
        tq_account="13800000000",
        tq_password="pwd",
        symbols=["SHFE.au2510"],
        enabled=True,
    )
    fields.update(overrides)
    return Account(**fields)


def _make_config(**overrides):
    fields = dict(
        server_url="http://127.0.0.1:3080",
        auto_trade=False,
        database_path="data/client.db",
    )
    fields.update(overrides)
    return TradingConfiguration(**fields)


class SimulationPageTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.page = SimulationPage()

    def test_set_account_fills_form(self):
        # 模拟页读写 accounts 表中的模拟账户记录
        self.page.set_account(_make_account(tq_account="13800000000", tq_password="pwd"))
        self.assertEqual(self.page.sim_account_edit.text(), "13800000000")
        self.assertEqual(self.page.sim_password_edit.text(), "pwd")

    def test_save_passes_kuaichi_account(self):
        self.page.sim_account_edit.setText(" 13800000000 ")
        self.page.sim_password_edit.setText("pwd")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured.get("tq_account"), "13800000000")
        self.assertEqual(captured.get("tq_password"), "pwd")

    def test_password_visibility_toggle(self):
        self.page.sim_password_edit.setText("pwd")
        self.assertEqual(self.page.sim_password_edit.echoMode(), QLineEdit.Password)
        hidden_icon = self.page.sim_password_toggle.icon().pixmap(36, 36).toImage()
        self.assertFalse(hidden_icon.isNull())
        self.page.sim_password_toggle.click()
        self.assertEqual(self.page.sim_password_edit.echoMode(), QLineEdit.Normal)
        visible_icon = self.page.sim_password_toggle.icon().pixmap(36, 36).toImage()
        self.assertNotEqual(hidden_icon, visible_icon)
        self.page.sim_password_toggle.click()
        self.assertEqual(self.page.sim_password_edit.echoMode(), QLineEdit.Password)
        self.assertEqual(
            hidden_icon, self.page.sim_password_toggle.icon().pixmap(36, 36).toImage()
        )

    def test_save_blocked_when_account_empty(self):
        self.page.sim_password_edit.setText("pwd")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured, {})

    def test_save_blocked_when_password_empty(self):
        self.page.sim_account_edit.setText("13800000000")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured, {})

    def test_test_connection_passes_credentials_and_disables_button(self):
        self.page.sim_account_edit.setText(" 13800000000 ")
        self.page.sim_password_edit.setText("pwd")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_test = lambda account, pwd: captured.update(
                account=account, pwd=pwd
            )
            self.page.test_btn.click()
        self.assertEqual(captured.get("account"), "13800000000")
        self.assertEqual(captured.get("pwd"), "pwd")
        self.assertFalse(self.page.test_btn.isEnabled())
        self.assertEqual(self.page.test_btn.text(), "测试中...")

    def test_test_connection_blocked_when_account_empty(self):
        self.page.sim_password_edit.setText("pwd")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_test = lambda account, pwd: captured.update(account=account)
            self.page.test_btn.click()
        self.assertEqual(captured, {})
        self.assertTrue(self.page.test_btn.isEnabled())

    def test_set_test_result_restores_button(self):
        self.page.test_btn.setEnabled(False)
        self.page.test_btn.setText("测试中...")
        with patch("src.presentation.pages.QMessageBox"):
            self.page.set_test_result("连接成功，账户密码验证通过", True)
        self.assertTrue(self.page.test_btn.isEnabled())
        self.assertEqual(self.page.test_btn.text(), "测试连接")

    def test_on_symbols_fetched_refills_and_restores_refresh_button(self):
        self.page.symbols_picker.set_fetching(True)
        self.assertFalse(self.page.symbols_picker._refresh_btn.isEnabled())
        self.page.on_symbols_fetched(["IF", "IH"])
        self.assertEqual([r.text() for r in self.page.symbols_picker._radios], ["IF", "IH"])
        self.assertTrue(self.page.symbols_picker._refresh_btn.isEnabled())

    def test_on_symbols_fetched_keeps_stored_symbol_checked(self):
        self.page.set_account(_make_account(symbols=["IH"]))
        self.page.on_symbols_fetched(["IF", "IH"])
        self.assertEqual(self.page.selected_symbol(), "IH")

    def test_selected_symbol_falls_back_when_list_not_fetched(self):
        # 列表未获取时回退账户已存品种；0 个或 2 个不猜测
        self.page.set_account(_make_account(symbols=["IH"]))
        self.assertEqual(self.page.selected_symbol(), "IH")
        self.page.set_account(_make_account(symbols=[]))
        self.assertEqual(self.page.selected_symbol(), "")
        self.page.set_account(_make_account(symbols=["IF", "IH"]))
        self.assertEqual(self.page.selected_symbol(), "")

    def test_save_omits_symbols_when_picker_empty(self):
        # 品种列表未获取时不提交 symbols，避免清空已有选择
        self.page.sim_account_edit.setText("13800000000")
        self.page.sim_password_edit.setText("pwd")
        self.assertFalse(self.page.symbols_picker.has_options())
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertNotIn("symbols", captured)

    def test_save_includes_selected_symbol(self):
        self.page.sim_account_edit.setText("13800000000")
        self.page.sim_password_edit.setText("pwd")
        self.page.symbols_picker.set_symbols(["IF", "IH"], selected="IF")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured.get("symbols"), ["IF"])

    def test_save_blocked_when_options_loaded_but_none_selected(self):
        self.page.sim_account_edit.setText("13800000000")
        self.page.sim_password_edit.setText("pwd")
        self.page.symbols_picker.set_symbols(["IF", "IH"], selected="")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured, {})

    def test_sim_account_inputs_labeled(self):
        # 第 3 步输入行须带「手机号：」「密码：」显式标签
        labels = [w.text() for w in self.page.findChildren(QLabel)]
        self.assertIn("手机号：", labels)
        self.assertIn("密码：", labels)
        self.assertEqual(self.page.sim_account_edit.placeholderText(), "手机号")
        self.assertEqual(self.page.sim_password_edit.placeholderText(), "密码")


class ConfigServiceLegacyDbTest(unittest.TestCase):
    """不含 sim 列的历史旧库：DROP 迁移与账户迁移对缺失列应无害，读写正常。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "client.db"
        conn = sqlite3.connect(self.db_path)
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
                initial_balance REAL NOT NULL,
                database TEXT NOT NULL,
                CHECK (id = 1)
            )
        """)
        conn.execute(
            "INSERT INTO app_config (id, server_url, symbols, auto_trade, tq_account, tq_password, initial_balance, database)"
            " VALUES (1, 'http://127.0.0.1:3080', '[\"SHFE.au2510\"]', 0, '13800000000', 'pwd', 1000000, ?)",
            (str(self.db_path),),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self._tmp.cleanup()

    def test_legacy_db_without_sim_columns_still_works(self):
        service = ConfigService(str(self.db_path))
        accounts = service.load_accounts()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].tq_account, "13800000000")
        self.assertEqual(accounts[0].tq_password, "pwd")


if __name__ == "__main__":
    unittest.main()
