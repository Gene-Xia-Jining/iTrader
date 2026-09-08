import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from ..application.bootstrap import Bootstrap
from ..application.trading_engine import TradingEngine
from ..domain.entities import TradingConfiguration
from ..domain.events import ConfigChangedEvent, LogEvent, LogLevel
from .main_window import MainWindow, ConfigDialog, DARK_QSS
from .viewmodels import MainViewModel


def make_tray_icon(size: int = 64) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    outer_rect = pix.rect().adjusted(2, 2, -2, -2)
    painter.setBrush(QColor("#1e1e2e"))
    painter.setPen(QColor("#45475a"))
    painter.drawRoundedRect(outer_rect, size // 8, size // 8)
    inner_size = size * 3 // 5
    inner_x = (size - inner_size) // 2
    inner_y = (size - inner_size) // 2
    painter.setBrush(QColor("#f9e2af"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(
        inner_x, inner_y, inner_size, inner_size,
        size // 12, size // 12,
    )
    painter.end()
    return QIcon(pix)


class AppController(QObject):
    engine_started = Signal()
    engine_stopped = Signal()
    quit_requested = Signal()

    def __init__(self, qt_app: QApplication, workdir: Path):
        super().__init__()
        self.qt_app = qt_app
        self.workdir = workdir
        self.bootstrap = Bootstrap(workdir / "config.toml")
        self._loop: asyncio.AbstractEventLoop | None = None
        self._engine: Optional[TradingEngine] = None
        self._engine_task: Optional[asyncio.Task] = None
        self._vm: Optional[MainViewModel] = None
        self._window: Optional[MainWindow] = None
        self._tray: Optional[QSystemTrayIcon] = None
        self._qt_poll_timer: Optional[QTimer] = None

    # -------- Lifecycle --------

    def start(self):
        config = self.bootstrap.config
        self._vm = MainViewModel(self.bootstrap.event_bus, config, self.qt_app)
        self._window = MainWindow(
            vm=self._vm,
            on_start=self._handle_start,
            on_stop=self._handle_stop,
            on_toggle_auto_trade=self._handle_toggle_auto_trade,
            on_open_config=self._handle_open_config,
            on_clear_logs=self._handle_clear_logs,
            on_show_about=self._handle_show_about,
            on_quit=self._handle_quit,
        )
        self._setup_tray()
        self._window.show()
        self._start_async_loop_on_thread()

    def _start_async_loop_on_thread(self):
        import threading

        loop = asyncio.new_event_loop()
        self._loop = loop

        def run_loop():
            asyncio.set_event_loop(loop)
            try:
                loop.run_forever()
            finally:
                try:
                    pending = asyncio.all_tasks(loop)
                    for t in pending:
                        t.cancel()
                    if pending:
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                except Exception:
                    pass
                loop.close()

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        # Qt -> asyncio: use a QTimer to periodically tick Qt while asyncio runs
        # Asyncio -> Qt: use QMetaObject.invokeMethod / queued connections
        self._qt_poll_timer = QTimer(self.qt_app)
        self._qt_poll_timer.setInterval(30)
        self._qt_poll_timer.timeout.connect(self._tick_qt)
        self._qt_poll_timer.start()

    def _tick_qt(self):
        pass

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = None
            return
        icon = make_tray_icon()
        tray = QSystemTrayIcon(icon, self.qt_app)
        tray.setToolTip("iTrader 交易客户端")

        menu = QMenu()

        show_action = QAction("显示主窗口", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        hide_action = QAction("隐藏主窗口", menu)
        hide_action.triggered.connect(self._hide_window)
        menu.addAction(hide_action)

        menu.addSeparator()

        start_action = QAction("启动自动交易", menu)
        start_action.triggered.connect(self._handle_start)
        menu.addAction(start_action)

        stop_action = QAction("停止自动交易", menu)
        stop_action.triggered.connect(self._handle_stop)
        menu.addAction(stop_action)

        menu.addSeparator()

        config_action = QAction("配置设置...", menu)
        config_action.triggered.connect(self._handle_open_config)
        menu.addAction(config_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._handle_quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray = tray

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self._window is None:
                return
            if self._window.isVisible():
                self._hide_window()
            else:
                self._show_window()

    def _show_window(self):
        if self._window is None:
            return
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()

    def _hide_window(self):
        if self._window is None:
            return
        self._window.hide()

    # -------- Handlers (UI thread) --------

    def _handle_start(self):
        if self._engine is not None and self._engine.is_running:
            return
        self._run_async(self._start_engine())

    def _handle_stop(self):
        if self._engine is None:
            return
        self._run_async(self._stop_engine())

    def _handle_toggle_auto_trade(self, value: bool):
        if self._engine is not None:
            self._engine.set_auto_trade(value)
        if self._vm is not None:
            self._vm.setAutoTrade(value)

    def _handle_open_config(self):
        if self._vm is None or self._window is None:
            return
        current_config = self._vm.config
        dlg = ConfigDialog(self._window, current_config)
        if dlg.exec() == ConfigDialog.Accepted and dlg.result_dict is not None:
            data = dlg.result_dict
            new_config = TradingConfiguration(
                server_url=data["server_url"],
                symbols=data["symbols"],
                auto_trade=data["auto_trade"],
                tq_account=data["tq_account"],
                tq_password=data["tq_password"],
                initial_balance=data["initial_balance"],
                database_path=current_config.database_path,
                client_cert_path=current_config.client_cert_path,
                client_key_path=current_config.client_key_path,
                ca_cert_path=current_config.ca_cert_path,
                enrollment_url=current_config.enrollment_url,
            )
            self.bootstrap.save_config(new_config)
            self._vm.update_config(new_config)
            self.bootstrap.event_bus.publish(ConfigChangedEvent())
            if self._engine is not None and self._engine.is_running:
                self.bootstrap.event_bus.publish(
                    LogEvent(message="配置已更新（下次启动生效）", level=LogLevel.WARNING)
                )
            else:
                self.bootstrap.reset_engine()
                self._engine = None
                self.bootstrap.event_bus.publish(
                    LogEvent(message="配置已保存", level=LogLevel.INFO)
                )

    def _handle_clear_logs(self):
        if self._window is not None:
            self._window.clear_logs()

    def _handle_show_about(self):
        if self._window is not None:
            self._window.show_about()

    def _handle_quit(self):
        running = self._engine is not None and self._engine.is_running
        if running and self._window is not None:
            if not self._window.ask_confirm_quit():
                return
        self._run_async(self._shutdown())

    # -------- Async helpers --------

    def _run_async(self, coro):
        if self._loop is None:
            return
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut

    async def _start_engine(self):
        if self._engine is None:
            self._engine = await self.bootstrap.build_engine()
        # apply current auto_trade state from VM
        if self._vm is not None:
            self._engine.set_auto_trade(self._vm.autoTrade)
        try:
            self._engine_task = asyncio.create_task(self._engine.start())
            self.engine_started.emit()
        except Exception as e:
            self.bootstrap.event_bus.publish(
                LogEvent(message=f"启动交易引擎失败: {e}", level=LogLevel.ERROR)
            )

    async def _stop_engine(self):
        if self._engine is None:
            return
        try:
            await self._engine.stop()
            if self._engine_task is not None and not self._engine_task.done():
                try:
                    await asyncio.wait_for(self._engine_task, timeout=5)
                except Exception:
                    pass
        except Exception as e:
            self.bootstrap.event_bus.publish(
                LogEvent(message=f"停止交易引擎失败: {e}", level=LogLevel.ERROR)
            )
        finally:
            self._engine = None
            self._engine_task = None
            self.engine_stopped.emit()

    async def _shutdown(self):
        await self._stop_engine()
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        # Schedule UI quit via Qt event loop
        QTimer.singleShot(50, self.qt_app.quit)
