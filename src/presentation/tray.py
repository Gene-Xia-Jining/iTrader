"""System tray (menu bar) UI for iTrader."""


import sys
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .viewmodels import MainViewModel


def _resource_path(name: str) -> Path:
    """Resolve a resource path for both dev and PyInstaller-frozen runs."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "resources" / name


def _draw_icon(size: int = 64) -> QIcon:
    """Programmatic fallback icon (near-black rounded square with an Action Blue block)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    outer_rect = pix.rect().adjusted(2, 2, -2, -2)
    painter.setBrush(QColor("#272729"))
    painter.setPen(QColor("#3a3a3c"))
    painter.drawRoundedRect(outer_rect, size // 8, size // 8)
    inner_size = size * 3 // 5
    inner_x = (size - inner_size) // 2
    inner_y = (size - inner_size) // 2
    painter.setBrush(QColor("#2997ff"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(
        inner_x, inner_y, inner_size, inner_size,
        size // 12, size // 12,
    )
    painter.end()
    return QIcon(pix)


def make_tray_icon() -> QIcon:
    """Load resources/icon.png, falling back to a programmatic icon."""
    path = _resource_path("icon.png")
    if path.exists():
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon
    return _draw_icon()


class TrayApp(QObject):
    """System tray icon with a status menu.

    Left-click (or double-click) on the tray icon shows the main window;
    right-click pops up the menu with status, config, about and quit actions.
    """

    def __init__(
        self,
        qt_app: QApplication,
        vm: MainViewModel,
        on_show_window: Callable[[], None],
        on_open_config: Callable[[], None],
        on_show_about: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        super().__init__()
        self._qt_app = qt_app
        self._vm = vm
        self._on_show_window = on_show_window
        self._menu: Optional[QMenu] = None
        self._tray: Optional[QSystemTrayIcon] = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(make_tray_icon(), qt_app)

        self._build_menu(on_show_window, on_open_config, on_show_about, on_quit)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

        self._bind_vm()
        self._refresh_status()

    # -------- Menu --------

    def _build_menu(
        self,
        on_show_window: Callable[[], None],
        on_open_config: Callable[[], None],
        on_show_about: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        menu = QMenu()
        self._menu = menu

        self._server_status_action = QAction(menu)
        self._server_status_action.setEnabled(False)
        menu.addAction(self._server_status_action)

        self._trade_status_action = QAction(menu)
        self._trade_status_action.setEnabled(False)
        menu.addAction(self._trade_status_action)

        menu.addSeparator()

        show_action = QAction("显示/隐藏主窗口", menu)
        show_action.triggered.connect(on_show_window)
        menu.addAction(show_action)

        config_action = QAction("配置设置...", menu)
        config_action.triggered.connect(on_open_config)
        menu.addAction(config_action)

        menu.addSeparator()

        about_action = QAction("关于", menu)
        about_action.triggered.connect(on_show_about)
        menu.addAction(about_action)

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        menu.setParent(None)

    # -------- Status binding --------

    def _bind_vm(self) -> None:
        self._vm.serverStatusChanged.connect(self._refresh_status)
        self._vm.tradingStatusChanged.connect(self._refresh_status)

    def _refresh_status(self) -> None:
        if self._tray is None:
            return
        server_dot = "🟢" if self._vm.serverStatus == "已连接" else "🔴"
        self._server_status_action.setText(f"{server_dot} 服务器状态: {self._vm.serverStatus}")

        trade_dot = "🟢" if self._vm.tradingStatus == "运行中" else "⚪"
        self._trade_status_action.setText(f"{trade_dot} 交易状态: {self._vm.tradingStatus}")

    # -------- Activation --------

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._on_show_window()
        elif reason == QSystemTrayIcon.ContextMenu:
            self._menu.popup(QCursor.pos())
