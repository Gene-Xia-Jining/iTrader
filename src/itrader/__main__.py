import sys
import os
from pathlib import Path


def run_gui():
    workdir = Path.cwd()
    if getattr(sys, "frozen", False):
        workdir = Path.home() / ".itrader"
        workdir.mkdir(parents=True, exist_ok=True)
        os.chdir(workdir)
        Path("data").mkdir(parents=True, exist_ok=True)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("iTrader")
    qt_app.setOrganizationName("iTrader")
    qt_app.setQuitOnLastWindowClosed(False)

    default_font = QFont()
    default_font.setPointSize(13)
    qt_app.setFont(default_font)

    from itrader.presentation.app_controller import AppController

    controller = AppController(qt_app, workdir)
    controller.start()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    run_gui()
