import asyncio
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEventLoop, QObject, QMetaObject, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from ..application.bootstrap import Bootstrap
from ..application.trading_engine import TradingEngine
from ..domain.entities import TradingConfiguration
from ..domain.events import ConfigChangedEvent, LogEvent, LogLevel
from ..infrastructure.api.client import check_server_health
from .main_window import ConfigDialog, MainWindow
from .tray import TrayApp
from .viewmodels import MainViewModel

class AppController(QObject):
    engine_started = Signal()
    engine_stopped = Signal()
    quit_requested = Signal()
    token_status_changed = Signal(str)
    server_test_finished = Signal(str, bool)

    def __init__(self, qt_app, workdir: Path):
        super().__init__()
        self.qt_app = qt_app
        self.workdir = workdir
        self.bootstrap = Bootstrap(str(workdir / "data/client.db"))
        self._loop: asyncio.AbstractEventLoop | None = None
        self._engine: Optional[TradingEngine] = None
        self._engine_task: Optional[asyncio.Task] = None
        self._vm: Optional[MainViewModel] = None
        self._window: Optional[MainWindow] = None
        self._tray: Optional[TrayApp] = None
        self.token_status_changed.connect(self._on_token_status_changed)

    # -------- Lifecycle --------

    def start(self):
        config = self.bootstrap.config
        self._vm = MainViewModel(self.bootstrap.event_bus, config, self.qt_app)
        self._window = MainWindow(
            vm=self._vm,
            on_toggle_auto_trade=self._handle_toggle_trading,
            on_open_config=self._handle_open_config,
            on_open_token=self._handle_open_token,
            on_clear_logs=self._handle_clear_logs,
            on_show_about=self._handle_show_about,
            on_quit=self._handle_quit,
            on_save_config=self._handle_save_config,
            on_test_server=self.handle_test_server,
        )
        self.server_test_finished.connect(self._window.settings_page.server_test.set_result)
        self._setup_tray()
        self._start_async_loop_on_thread()

    def _start_async_loop_on_thread(self):
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

    def _setup_tray(self):
        self._tray = TrayApp(
            self.qt_app,
            self._vm,
            on_show_window=self._show_window,
            on_open_config=self._handle_open_config,
            on_show_about=self._handle_show_about,
            on_quit=self._handle_quit,
        )

    def _show_window(self):
        if self._window is None:
            return
        if self._window.isVisible():
            self._window.hide()
        else:
            self._window.showNormal()
            self._window.raise_()
            self._window.activateWindow()

    # -------- Handlers (UI thread) --------

    def _handle_open_token(self, description: str = ""):
        self._run_async(self._refresh_token_status())
        if description:
            self._run_async(self._request_token(description))

    def _handle_toggle_auto_trade(self, value: bool):
        if self._engine is not None:
            self._engine.set_auto_trade(value)
        if self._vm is not None:
            self._vm.setAutoTrade(value)

    def _handle_toggle_trading(self, value: bool):
        self._handle_toggle_auto_trade(value)
        if value:
            self._run_async(self._start_engine())
        else:
            self._run_async(self._stop_engine())
        if self._window is not None and self._vm is not None:
            self._show_blocking_toggle(lambda: self._vm.tradingActive == value)

    def _show_blocking_toggle(self, finished) -> None:
        """阻塞式提示框：等待切换完成后自动消失。"""
        dlg = QDialog(self._window)
        dlg.setWindowTitle("自动交易")
        dlg.setModal(True)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(dlg)
        label = QLabel("正在切换...")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        dlg.setFixedWidth(220)

        loop = QEventLoop()
        timer = QTimer(dlg)
        timer.setInterval(50)
        timeout = QTimer(dlg)
        timeout.setSingleShot(True)
        timeout.setInterval(30000)

        def done() -> None:
            timer.stop()
            timeout.stop()
            dlg.close()
            loop.quit()

        def check() -> None:
            if finished():
                done()

        timer.timeout.connect(check)
        timeout.timeout.connect(done)
        dlg.show()
        timer.start()
        timeout.start()
        loop.exec()

    def _handle_open_config(self):
        if self._vm is None:
            return
        current_config = self._vm.config
        parent = self._window if self._window is not None else None
        dlg = ConfigDialog(parent, current_config)
        dlg.server_test.on_test = self.handle_test_server
        self.server_test_finished.connect(dlg.server_test.set_result)
        try:
            accepted = dlg.exec() == ConfigDialog.Accepted
        finally:
            self.server_test_finished.disconnect(dlg.server_test.set_result)
        if accepted and dlg.result_dict is not None:
            data = dlg.result_dict
            new_config = TradingConfiguration(
                server_url=data["server_url"],
                symbols=data["symbols"],
                auto_trade=current_config.auto_trade,
                tq_account=data["tq_account"],
                tq_password=data["tq_password"],
                initial_balance=data["initial_balance"],
                database_path=current_config.database_path,
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

    def _handle_save_config(self, data: dict):
        """Handle saving configuration from the embedded settings page"""
        if self._vm is None:
            return
        current_config = self._vm.config
        # 设置页表单传来的是逗号分隔字符串和数字字符串，先转回领域模型类型
        symbols = [s.strip() for s in data["symbols"].split(",") if s.strip()]
        new_config = TradingConfiguration(
            server_url=data["server_url"],
            symbols=symbols,
            auto_trade=current_config.auto_trade,
            tq_account=data["tq_account"],
            tq_password=data["tq_password"],
            initial_balance=float(data["initial_balance"]),
            database_path=current_config.database_path,
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

    def handle_test_server(self, server_url: str):
        self._run_async(self._test_server(server_url))

    async def _test_server(self, server_url: str):
        try:
            await check_server_health(server_url)
        except Exception as e:
            self.server_test_finished.emit(f"连接失败: {e}", False)
        else:
            self.server_test_finished.emit("连接成功", True)

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

    def _on_token_status_changed(self, status: str):
        if self._window is not None:
            self._window.set_token_status(status)

    async def _refresh_token_status(self):
        try:
            data = await self.bootstrap.token_service.get_token_requests()
            status = "待审核"
            for request in data.get("tokens", data.get("requests", [])):
                if request.get("status") == "approved":
                    token = await self.bootstrap.token_service.load_approved_token(data)
                    if token:
                        status = f"已通过，已保存到 {self.bootstrap.token_store.token_dir}"
                    else:
                        status = "已通过，但服务器未返回 token"
                    break
            self.token_status_changed.emit(status)
        except Exception as e:
            self.token_status_changed.emit(f"查询失败: {e}")

    async def _request_token(self, description: str):
        try:
            await self.bootstrap.token_service.request_token(description or "iTrader 智能交易客户端")
            self.token_status_changed.emit("已提交申请，等待服务器审核")
            QTimer.singleShot(1500, lambda: self._run_async(self._refresh_token_status()))
        except Exception as e:
            self.token_status_changed.emit(f"申请失败: {e}")

    def save_approved_token(self, data: dict):
        async def _save():
            try:
                token = await self.bootstrap.token_service.load_approved_token(data)
                self.token_status_changed.emit(f"已通过，已保存到 {self.bootstrap.token_store.token_dir}" if token else "已通过，但服务器未返回 token")
            except Exception as e:
                self.token_status_changed.emit(f"保存 token 失败: {e}")
        self._run_async(_save())

    async def _start_engine(self):
        if self._engine is None:
            self._engine = await self.bootstrap.build_engine()
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

    @Slot()
    def do_quit(self):
        self.qt_app.quit()

    async def _shutdown(self):
        await self._stop_engine()
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        # _shutdown 运行在 asyncio 线程，QTimer.singleShot 的定时器没有事件循环可驱动，
        # 必须把退出动作排队到 UI 线程
        QMetaObject.invokeMethod(self, "do_quit", Qt.QueuedConnection)
