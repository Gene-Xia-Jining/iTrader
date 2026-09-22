import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from src.domain.entities import Account
from src.presentation.pages import BROKER_GROUPS, AccountPage, _AccountCard


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


def _make_account(**overrides):
    fields = dict(
        id="live-1",
        kind="live",
        label="实盘账户1",
        tq_account="13800000000",
        tq_password="pwd",
        broker="徽商期货",
        trade_account="123456",
        trade_password="trade-pwd",
        symbols=["SHFE.au2510"],
        enabled=True,
    )
    fields.update(overrides)
    return Account(**fields)


class AccountPageCardsTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.page = AccountPage()

    def test_add_card_creates_live_account_card(self):
        self.assertEqual(self.page.card_count(), 0)
        self.page.add_btn.click()
        self.assertEqual(self.page.card_count(), 1)

    def test_set_accounts_rebuilds_cards(self):
        accounts = [
            _make_account(id="live-1", label="实盘1"),
            _make_account(id="live-2", label="实盘2"),
            Account("legacy", "sim", "模拟账户", "13800000000", "pwd"),
        ]
        self.page.set_accounts(accounts)
        # 仅实盘账户在实盘交易页生成卡片
        self.assertEqual(self.page.card_count(), 2)

    def test_card_save_passes_account_data(self):
        card = _AccountCard("live-1", self.page, BROKER_GROUPS)
        card.fill(_make_account())
        captured = {}
        with patch("src.presentation.pages.QMessageBox"):
            card.on_save = lambda data: captured.update(data)
            card.save_btn.click()
        self.assertEqual(captured.get("account_id"), "live-1")
        self.assertEqual(captured.get("kind"), "live")
        self.assertEqual(captured.get("broker"), "徽商期货")
        self.assertEqual(captured.get("tq_account"), "13800000000")
        self.assertEqual(captured.get("trade_account"), "123456")


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
