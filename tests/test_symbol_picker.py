import unittest

from PySide6.QtWidgets import QApplication, QLabel

from src.presentation.pages import SimulationPage, SymbolPicker


def _make_app():
    app = QApplication.instance() or QApplication([])
    return app


def _texts(picker: SymbolPicker):
    return [radio.text() for radio in picker._radios]


class SymbolPickerTest(unittest.TestCase):
    def setUp(self):
        _make_app()
        self.picker = SymbolPicker()

    def test_set_symbols_builds_options_and_selects(self):
        self.picker.set_symbols(["IF", "IH"], selected="IH")
        self.assertEqual(_texts(self.picker), ["IF", "IH"])
        self.assertEqual(self.picker.get_selected(), "IH")
        self.assertTrue(self.picker.has_options())
        self.assertIn("共 2 个品种", self.picker._hint.text())

    def test_set_symbols_keeps_selected_not_in_server_list(self):
        # 已选但服务器未返回的品种保留，避免静默丢失
        self.picker.set_symbols(["IF", "IH"], selected="IH")
        self.picker.set_symbols(["IF"], selected="IH")
        self.assertEqual(_texts(self.picker), ["IF", "IH"])
        self.assertEqual(self.picker.get_selected(), "IH")

    def test_set_symbols_empty_list(self):
        self.picker.set_symbols([])
        self.assertEqual(self.picker._radios, [])
        self.assertFalse(self.picker.has_options())
        self.assertEqual(self.picker._hint.text(), "服务器暂无可订阅品种")

    def test_get_selected_empty_when_nothing_checked(self):
        self.picker.set_symbols(["IF", "IH"], selected="")
        self.assertFalse(self.picker.get_selected())

    def test_set_fetching_toggles_refresh_button(self):
        self.assertTrue(self.picker._refresh_btn.isEnabled())
        self.picker.set_fetching(True)
        self.assertFalse(self.picker._refresh_btn.isEnabled())
        self.assertEqual(self.picker._hint.text(), "正在获取品种...")
        self.picker.set_fetching(False)
        self.assertTrue(self.picker._refresh_btn.isEnabled())

    def test_set_fetch_error_restores_button_and_shows_message(self):
        self.picker.set_fetching(True)
        self.picker.set_fetch_error("连接超时")
        self.assertTrue(self.picker._refresh_btn.isEnabled())
        self.assertEqual(self.picker._hint.text(), "获取品种失败: 连接超时")

    def test_without_refresh_button_does_not_raise(self):
        picker = SymbolPicker(with_refresh=False)
        self.assertIsNone(picker._refresh_btn)
        picker.set_fetching(True)
        picker.set_fetching(False)
        picker.set_fetch_error("出错")
        self.assertFalse(picker.has_options())


class SimulationPageStepWordingTest(unittest.TestCase):
    """第 4 步引导文案：不出现已取消的「模拟交易账户」措辞。"""

    def setUp(self):
        _make_app()
        self.page = SimulationPage()

    def _step_labels(self):
        labels = [w.text() for w in self.page.findChildren(QLabel)]
        return [t for t in labels if t[:2] in ("1，", "2，", "3，", "4，", "5，")]

    def test_step4_mentions_symbols_only(self):
        steps = self._step_labels()
        self.assertIn("4，选择交易品种：", steps)
        self.assertEqual(steps[-1], "4，选择交易品种：")

    def test_no_step_mentions_simulated_account(self):
        for step in self._step_labels():
            self.assertNotIn("模拟交易账户", step)


if __name__ == "__main__":
    unittest.main()
