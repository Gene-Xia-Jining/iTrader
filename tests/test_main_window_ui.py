import unittest

from PySide6.QtWidgets import QApplication

from src.domain.entities import TradingConfiguration
from src.domain.events import EventBus, TradingStartedEvent, TradingStoppedEvent
from src.presentation.main_window import MainWindow
from src.presentation.viewmodels import MainViewModel


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


class MainWindowUiTest(unittest.TestCase):
    def setUp(self):
        _make_app()

    def test_navigation_callbacks_and_log_state(self):
        vm = MainViewModel(EventBus(), TradingConfiguration("http://localhost:8000", True))
        calls = []
        window = MainWindow(
            vm=vm,
            on_toggle_auto_trade=lambda value: calls.append(f"toggle:{value}"),
            on_open_config=lambda: calls.append("config"),
            on_open_token=lambda description="": calls.append(f"token:{description}"),
            on_clear_logs=lambda: calls.append("clear"),
            on_show_about=lambda: calls.append("about"),
            on_quit=lambda: calls.append("quit"),
            on_save_config=lambda data: calls.append(f"save:{data}"),
        )

        window._head_quit_btn.click()
        window.set_token_status("已通过")
        window._append_log("hello", "#a6e3a1")
        window.clear_logs()
        window.resize(900, 600)
        window.resize(1400, 900)

        self.assertEqual(calls, ["quit"])
        self.assertTrue(window.token_page.token_status_btn.isEnabled())
        self.assertEqual(window.log_page.log_view.toPlainText(), "")
        self.assertEqual(window.account_btn.accessibleName(), "实盘交易")
        self.assertEqual(window.simulation_btn.accessibleName(), "模拟交易")

    def test_head_auto_trade_button_follows_engine_state(self):
        bus = EventBus()
        vm = MainViewModel(bus, TradingConfiguration("http://localhost:8000", True))
        calls = []
        window = MainWindow(
            vm=vm,
            on_toggle_auto_trade=lambda value: calls.append(f"toggle:{value}"),
            on_open_config=lambda: calls.append("config"),
            on_open_token=lambda description="": calls.append(f"token:{description}"),
            on_clear_logs=lambda: calls.append("clear"),
            on_show_about=lambda: calls.append("about"),
            on_quit=lambda: calls.append("quit"),
            on_save_config=lambda data: calls.append(f"save:{data}"),
        )

        # 引擎未运行时按钮显示"关"，即使配置里 auto_trade=True
        self.assertEqual(window._head_auto_btn.text(), "自动交易：关")
        self.assertEqual(window._head_auto_btn.property("variant"), "secondary")

        window._head_auto_btn.click()
        self.assertEqual(calls, ["toggle:True"])

        bus.publish(TradingStartedEvent())
        self.assertEqual(window._head_auto_btn.text(), "自动交易：开")
        self.assertEqual(window._head_auto_btn.property("variant"), "success")

        window._head_auto_btn.click()
        self.assertEqual(calls, ["toggle:True", "toggle:False"])

        bus.publish(TradingStoppedEvent())
        self.assertEqual(window._head_auto_btn.text(), "自动交易：关")
        self.assertEqual(window._head_auto_btn.property("variant"), "secondary")


if __name__ == "__main__":
    unittest.main()
