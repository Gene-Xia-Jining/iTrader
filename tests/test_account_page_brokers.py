import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from src.infrastructure.config.broker_store import DEFAULT_GROUPS, BrokerStore
from src.presentation.pages import AccountPage


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


class BrokerStoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "broker.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_load_writes_default_file_when_missing(self):
        store = BrokerStore(str(self.path))
        data = store.load()
        self.assertEqual(data["groups"], DEFAULT_GROUPS)
        self.assertEqual(data["selected"], "宏源期货")
        self.assertTrue(self.path.exists())
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["groups"], DEFAULT_GROUPS)

    def test_save_selected_updates_file(self):
        store = BrokerStore(str(self.path))
        store.load()
        store.save_selected("光大期货")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["selected"], "光大期货")
        self.assertEqual(data["groups"], DEFAULT_GROUPS)

    def test_load_falls_back_when_file_corrupted(self):
        self.path.write_text("{not json", encoding="utf-8")
        store = BrokerStore(str(self.path))
        data = store.load()
        self.assertEqual(data["groups"], DEFAULT_GROUPS)
        self.assertEqual(data["selected"], "")


class AccountPageBrokerTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.page = AccountPage()

    def test_set_brokers_builds_grouped_radios(self):
        self.page.set_brokers(DEFAULT_GROUPS, "")
        radios = self.page._broker_group.buttons()
        self.assertEqual(
            [radio.text() for radio in radios],
            ["宏源期货", "徽商期货", "银河期货", "东方汇金", "光大期货", "国泰君安"],
        )
        # 未提供选中项时默认选第一项
        self.assertTrue(radios[0].isChecked())

    def test_single_selection_across_groups(self):
        self.page.set_brokers(DEFAULT_GROUPS, "徽商期货")
        radios = self.page._broker_group.buttons()
        self.assertTrue(radios[1].isChecked())
        # 免费/专业版分属不同父级容器，跨组选择时旧选中项必须被取消
        radios[4].setChecked(True)
        self.assertEqual(self.page._selected_broker(), "光大期货")

    def test_save_includes_selected_broker(self):
        self.page.set_brokers(DEFAULT_GROUPS, "银河期货")
        self.page.tq_account_edit.setText("acc")
        self.page.tq_password_edit.setText("pwd")
        self.page.balance_edit.setText("1000000")
        self.page.symbols_edit.setText("SHFE.au2510")
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            self.page.on_save = lambda data: captured.update(data)
            self.page.save_btn.click()
        self.assertEqual(captured.get("broker"), "银河期货")
        self.assertEqual(captured.get("tq_account"), "acc")


if __name__ == "__main__":
    unittest.main()
