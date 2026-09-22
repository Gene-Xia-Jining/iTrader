import asyncio
import shutil
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEventLoop, QObject, QMetaObject, Qt, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from .. import __version__
from ..application.bootstrap import Bootstrap
from ..application.trading_engine import TradingEngine
from ..domain.entities import Account, TradingConfiguration
from ..domain.events import ConfigChangedEvent, LogEvent, LogLevel
from ..infrastructure.api.client import (
    check_server_health,
    fetch_server_symbols,
)
from ..infrastructure.proxy import apply_proxy_environment, server_host
from ..infrastructure.trading.tqsdk_executor import test_tq_auth_connection
from ..infrastructure.updater import (
    RELEASE_PAGE_URL,
    ReleaseInfo,
    apply_update_and_restart,
    cleanup_stale_backups,
    download_release,
    extract_update,
    fetch_latest_release,
    is_newer,
)
from .main_window import ConfigDialog, MainWindow
from .pages import BROKER_GROUPS
from .tray import TrayApp
from .viewmodels import MainViewModel

class AppController(QObject):
    engine_started = Signal()
    engine_stopped = Signal()
    quit_requested = Signal()
    token_status_changed = Signal(str)
    server_test_finished = Signal(str, bool)
    sim_test_finished = Signal(str, bool)
    symbols_fetched = Signal(bool, str, object)
    auto_trade_rejected = Signal()
    # 自动更新：信号从 asyncio 线程回 UI 线程
    # update_check_finished 第二参为 True/False/None（成功/失败/进行中），
    # 用 object 透传 None，避免被 bool 信号强转为 False
    update_available = Signal(object, bool)
    update_check_finished = Signal(str, object)
    update_download_progress = Signal(int, int, int)
    update_ready = Signal(str)
    update_failed = Signal(str)
    update_download_cancelled = Signal()

    def __init__(self, qt_app, workdir: Path):
        super().__init__()
        self.qt_app = qt_app
        self.workdir = workdir
        self.bootstrap = Bootstrap(str(workdir / "data/client.db"))
        self._loop: asyncio.AbstractEventLoop | None = None
        # 每个启用账户一个引擎，可同时运行
        self._engines: dict[str, TradingEngine] = {}
        self._engine_tasks: dict[str, asyncio.Task] = {}
        self._vm: Optional[MainViewModel] = None
        self._window: Optional[MainWindow] = None
        self._tray: Optional[TrayApp] = None
        self._toggle_rejected = False
        # 自动更新状态：已发现的版本 / 下载任务 / 暂存路径 / 包类型
        self._release: Optional[ReleaseInfo] = None
        self._update_future = None
        self._staged_item: Optional[Path] = None
        self._update_kind = "full"
        self.token_status_changed.connect(self._on_token_status_changed)

    # -------- Lifecycle --------

    def start(self):
        config = self.bootstrap.config
        self._vm = MainViewModel(self.bootstrap.event_bus, config, self.qt_app)
        # 清理上次更新遗留的 .old-* 备份（失败不影响启动）
        cleanup_stale_backups()
        # 在任何网络请求发生前应用代理设置（默认强制直连，屏蔽系统代理）
        self._apply_proxy_env(config)
        self._window = MainWindow(
            vm=self._vm,
            on_toggle_auto_trade=self._handle_toggle_trading,
            on_open_config=self._handle_open_config,
            on_open_token=self._handle_open_token,
            on_clear_logs=self._handle_clear_logs,
            on_show_about=self._handle_show_about,
            on_quit=self._handle_quit,
            on_save_config=self._handle_save_config,
            on_save_account=self._handle_save_account,
            on_save_simulation=self._handle_save_simulation,
            on_test_simulation=self.handle_test_simulation,
            on_test_server=self.handle_test_server,
            on_fetch_symbols=self.handle_fetch_symbols,
            on_check_update=self.handle_check_update,
            on_cancel_update=self.handle_cancel_update,
        )
        self._window.account_page.on_delete = self._handle_delete_account
        # 初始回填账户数据到实盘卡片与模拟表单
        self._sync_accounts_to_ui()
        self.server_test_finished.connect(self._window.settings_page.server_test.set_result)
        self.sim_test_finished.connect(self._window.simulation_page.set_test_result)
        self.symbols_fetched.connect(self._on_symbols_fetched)
        self.auto_trade_rejected.connect(self._window.show_server_not_connected)
        self.update_available.connect(self._on_update_available)
        self.update_check_finished.connect(self._window.settings_page.set_update_status)
        self.update_download_progress.connect(self._window.set_update_progress)
        self.update_ready.connect(self._on_update_ready)
        self.update_failed.connect(self._on_update_failed)
        self.update_download_cancelled.connect(self._on_update_cancelled)
        self._setup_tray()
        self._start_async_loop_on_thread()
        self._schedule_startup_update_check()

    def _schedule_startup_update_check(self):
        """启动后延迟静默检查更新，避免与行情/服务器连接争抢网络。"""
        if self._vm is None or not self._vm.config.auto_check_update:
            return
        QTimer.singleShot(5000, lambda: self.handle_check_update(silent=True))

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
        for engine in self._engines.values():
            engine.set_auto_trade(value)
        if self._vm is not None:
            self._vm.setAutoTrade(value)

    def _handle_toggle_trading(self, value: bool):
        if value:
            # 开启前先探测服务器连通性，未连接则提示并取消切换
            self._toggle_rejected = False
            self._run_async(self._start_engines_checked())
            if self._window is not None and self._vm is not None:
                self._show_blocking_toggle(
                    lambda: self._vm.tradingActive or self._toggle_rejected
                )
        else:
            self._handle_toggle_auto_trade(False)
            self._run_async(self._stop_engines())
            if self._window is not None and self._vm is not None:
                self._show_blocking_toggle(lambda: not self._vm.tradingActive)

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

    def _apply_proxy_env(self, config: TradingConfiguration):
        """按配置设置代理环境变量（默认不走代理）。"""
        hosts = [server_host(config.server_url)] if config.server_url else []
        apply_proxy_environment(config.proxy_url, hosts)

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
                auto_trade=current_config.auto_trade,
                proxy_url=current_config.proxy_url,
                auto_check_update=current_config.auto_check_update,
                skipped_version=current_config.skipped_version,
                database_path=current_config.database_path,
            )
            self.bootstrap.save_config(new_config)
            self._vm.update_config(new_config)
            self.bootstrap.event_bus.publish(ConfigChangedEvent())
            if any(e.is_running for e in self._engines.values()):
                self.bootstrap.event_bus.publish(
                    LogEvent(message="配置已更新（下次启动生效）", level=LogLevel.WARNING)
                )
            else:
                self.bootstrap.reset_engine()
                self._engines.clear()
                self._engine_tasks.clear()
                self.bootstrap.event_bus.publish(
                    LogEvent(message="配置已保存", level=LogLevel.INFO)
                )

    def _handle_save_config(self, data: dict):
        """保存来自设置页的服务器连接配置（data 为部分字段）。"""
        self._apply_partial_config(data)

    def _handle_save_account(self, data: dict):
        """保存来自交易账号页的实盘账户。期货公司随账户记录存储。"""
        self._save_account(data, "live")

    def _handle_save_simulation(self, data: dict):
        """保存来自模拟交易页的快期模拟账户。"""
        self._save_account(data, "sim")

    def _save_account(self, data: dict, kind: str) -> None:
        """把表单数据存为一条账户记录。

        UI 过渡期：未携带 account_id 时落到固定 id（sim→legacy、live→legacy-live），
        与旧版单账户配置的迁移记录对齐，保证迁移后仍可编辑。
        """
        if self._vm is None:
            return
        symbols_raw = data.get("symbols")
        if isinstance(symbols_raw, str):
            symbols = [s.strip() for s in symbols_raw.split(",") if s.strip()]
        elif isinstance(symbols_raw, list):
            symbols = [str(s) for s in symbols_raw]
        else:
            symbols = None  # 未提供时沿用已有账户的品种

        account_id = data.get("account_id") or ("legacy" if kind == "sim" else "legacy-live")
        existing = self.bootstrap.config_service.get_account(account_id)
        account = Account(
            id=account_id,
            kind=kind,
            label=data.get("label") or (existing.label if existing else ("模拟账户" if kind == "sim" else "实盘账户")),
            tq_account=data.get("tq_account") or (existing.tq_account if existing else ""),
            tq_password=data.get("tq_password") or (existing.tq_password if existing else ""),
            broker=data.get("broker") or (existing.broker if existing else ""),
            trade_account=data.get("trade_account") or (existing.trade_account if existing else ""),
            trade_password=data.get("trade_password") or (existing.trade_password if existing else ""),
            symbols=symbols if symbols is not None else (list(existing.symbols) if existing else []),
            enabled=data.get("enabled", existing.enabled if existing else True),
        )
        self.bootstrap.save_account(account)
        self._on_accounts_changed()

    def _on_accounts_changed(self) -> None:
        """账户变更后的引擎与状态同步。"""
        self._sync_accounts_to_ui()
        self.bootstrap.event_bus.publish(ConfigChangedEvent())
        if any(e.is_running for e in self._engines.values()):
            self.bootstrap.event_bus.publish(
                LogEvent(message="账户配置已更新（下次启动生效）", level=LogLevel.WARNING)
            )
        else:
            self.bootstrap.reset_engine()
            self._engines.clear()
            self._engine_tasks.clear()
            self.bootstrap.event_bus.publish(LogEvent(message="账户配置已保存", level=LogLevel.INFO))

    def _apply_partial_config(self, data: dict):
        """保存全局配置（与账户无关的项）。"""
        if self._vm is None:
            return
        current = self._vm.config
        new_config = TradingConfiguration(
            server_url=data.get("server_url", current.server_url),
            auto_trade=current.auto_trade,
            proxy_url=data.get("proxy_url", current.proxy_url),
            auto_check_update=data.get("auto_check_update", current.auto_check_update),
            skipped_version=data.get("skipped_version", current.skipped_version),
            database_path=current.database_path,
        )
        self.bootstrap.save_config(new_config)
        self._vm.update_config(new_config)
        self._apply_proxy_env(new_config)
        self._on_accounts_changed()

    def _handle_clear_logs(self):
        if self._window is not None:
            self._window.clear_logs()

    def handle_test_server(self, server_url: str):
        self._run_async(self._test_server(server_url))

    def handle_test_simulation(self, account: str, password: str):
        self._run_async(self._test_simulation(account, password))

    async def _test_simulation(self, account: str, password: str):
        # TqApi 构造是阻塞网络调用，放线程池避免卡住 asyncio 事件循环
        try:
            await asyncio.to_thread(test_tq_auth_connection, account, password)
        except Exception as e:
            self.sim_test_finished.emit(f"连接失败: {e}", False)
        else:
            self.sim_test_finished.emit("连接成功，账户密码验证通过", True)

    async def _test_server(self, server_url: str):
        try:
            await check_server_health(server_url)
        except Exception as e:
            self.server_test_finished.emit(f"连接失败: {e}", False)
        else:
            self.server_test_finished.emit("连接成功", True)

    def handle_fetch_symbols(self):
        # 调用方（切页、刷新按钮）都不传地址，统一从配置取
        self._run_async(self._fetch_symbols())

    async def _fetch_symbols(self):
        server_url = self.bootstrap.config.server_url
        if not server_url:
            self.symbols_fetched.emit(False, "未配置服务器地址", [])
            return
        try:
            symbols = await fetch_server_symbols(
                server_url, token_service=self.bootstrap.token_service
            )
        except Exception as e:
            self.symbols_fetched.emit(False, f"获取失败: {e}", [])
        else:
            self.symbols_fetched.emit(True, f"获取成功，共 {len(symbols)} 个品种", symbols)

    def _on_symbols_fetched(self, success: bool, message: str, symbols: list):
        if not self._window:
            return
        if success:
            self._window.simulation_page.on_symbols_fetched(symbols)
            for card in self._window.account_page._cards.values():
                card.symbols_picker.set_symbols(symbols, selected=card.symbols_picker.get_selected())
        else:
            self._window.simulation_page.symbols_picker.set_fetch_error(message)

    def _handle_delete_account(self, account_id: str):
        self.bootstrap.delete_account(account_id)
        self._on_accounts_changed()

    def _sync_accounts_to_ui(self):
        if not self._window:
            return
        accounts = self.bootstrap.accounts
        self._window.account_page.set_accounts(accounts)
        sim = next((a for a in accounts if a.kind == "sim"), None)
        self._window.simulation_page.set_account(sim)
        self._window.sync_accounts_to_dashboard(accounts)

    def _handle_show_about(self):
        if self._window is not None:
            self._window.show_about()

    # -------- 自动更新 (UI thread handlers) --------

    def handle_check_update(self, silent: bool = False):
        self._run_async(self._check_update(silent))

    def handle_cancel_update(self):
        if self._update_future is not None:
            self._update_future.cancel()

    def handle_apply_update(self):
        """确认重启后：先停引擎释放连接，再替换安装物并启动新进程，最后退出。"""
        if self._staged_item is None:
            return
        running = any(e.is_running for e in self._engines.values())
        if running and self._window is not None and not self._window.ask_confirm_quit():
            return

        async def _apply_and_quit():
            # 先完全停止所有交易引擎并释放所有网络/数据库资源，消除新旧进程重叠并发
            await self._stop_engines()
            await self.bootstrap.shutdown()
            try:
                apply_update_and_restart(self._staged_item, self._update_kind)
            except Exception as e:
                self.update_failed.emit(f"安装更新失败: {e}")
                return
            await self._shutdown()

        self._run_async(_apply_and_quit())

    async def _check_update(self, silent: bool):
        try:
            release = await fetch_latest_release()
        except Exception as e:
            if not silent:
                self.update_check_finished.emit(f"检查更新失败: {e}", False)
            return
        if release is None:
            if not silent:
                self.update_check_finished.emit("未找到可用的更新包", False)
            return
        if not is_newer(release.version, __version__):
            if not silent:
                self.update_check_finished.emit(f"已是最新版本（v{__version__}）", True)
            return
        # 静默检查尊重"跳过此版本"；手动检查不受影响
        if silent and self._vm is not None and release.version == self._vm.config.skipped_version:
            return
        # 手动检查发现新版本：先回写状态恢复设置页按钮，再弹更新对话框
        if not silent:
            self.update_check_finished.emit(f"发现新版本 v{release.version}", None)
        self._release = release
        self.update_available.emit(release, silent)

    def handle_download_update(self):
        release = self._release
        if release is None or self._window is None:
            return
        # 有补丁包时差量更新，否则回退全量
        use_patch = release.has_patch
        self._update_kind = "patch" if use_patch else "full"
        url = release.patch_url if use_patch else release.full_url
        self._window.begin_update_progress()
        self._update_future = self._run_async(self._download_update(url))

    async def _download_update(self, url: str):
        stage_dir = self._stage_dir()
        last_pct = -1

        def progress(received: int, total: int):
            nonlocal last_pct
            if total <= 0:
                # 服务器未返回总大小时仅更新已下载量文本
                self.update_download_progress.emit(-1, received, total)
                return
            pct = min(100, int(received * 100 / total))
            if pct != last_pct:
                last_pct = pct
                self.update_download_progress.emit(pct, received, total)

        try:
            zip_path = await download_release(url, stage_dir, progress_cb=progress)
            self._staged_item = await asyncio.to_thread(
                extract_update, zip_path, stage_dir
            )
        except asyncio.CancelledError:
            self.update_download_cancelled.emit()
            return
        except Exception as e:
            self.update_failed.emit(f"下载更新失败: {e}")
            return
        self.update_ready.emit("差量更新包" if self._update_kind == "patch" else "完整更新包")

    def _on_update_available(self, release: ReleaseInfo, silent: bool):
        if self._window is None:
            return
        choice = self._window.show_update_available(release)
        if choice == "update":
            self.handle_download_update()
        elif choice == "skip":
            self._skip_version(release.version)
        elif choice == "page":
            QDesktopServices.openUrl(QUrl(RELEASE_PAGE_URL))

    def _on_update_ready(self, kind_label: str):
        if self._window is None:
            return
        self._window.finish_update_progress()
        if self._window.show_update_ready(kind_label):
            self.handle_apply_update()

    def _on_update_failed(self, message: str):
        self._update_future = None
        self._clear_stage_dir()
        if self._window is not None:
            self._window.finish_update_progress()
            self._window.show_update_error(message)

    def _on_update_cancelled(self):
        self._update_future = None
        self._clear_stage_dir()
        if self._window is not None:
            self._window.finish_update_progress()
            self._window.settings_page.set_update_status("已取消下载", False)

    def _skip_version(self, version: str):
        if self._vm is None:
            return
        self._apply_partial_config({"skipped_version": version})

    def _stage_dir(self) -> Path:
        return self.workdir / "data" / "update"

    def _clear_stage_dir(self):
        # 暂存目录只存可重新下载的更新包，清理失败仅占磁盘，不影响功能
        shutil.rmtree(self._stage_dir(), ignore_errors=True)
        self._staged_item = None

    def _handle_quit(self):
        running = any(e.is_running for e in self._engines.values())
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
                        status = "已通过，token 已加密保存"
                    else:
                        status = "已通过，但服务器未返回 token"
                    break
            self.token_status_changed.emit(status)
        except Exception as e:
            self.token_status_changed.emit(f"查询失败: {e}")

    async def _request_token(self, description: str):
        try:
            await self.bootstrap.token_service.request_token(description or "iTrader 智能交易系统")
            self.token_status_changed.emit("已提交申请，等待服务器审核")
            QTimer.singleShot(1500, lambda: self._run_async(self._refresh_token_status()))
        except Exception as e:
            self.token_status_changed.emit(f"申请失败: {e}")

    def save_approved_token(self, data: dict):
        async def _save():
            try:
                token = await self.bootstrap.token_service.load_approved_token(data)
                self.token_status_changed.emit("已通过，token 已加密保存" if token else "已通过，但服务器未返回 token")
            except Exception as e:
                self.token_status_changed.emit(f"保存 token 失败: {e}")
        self._run_async(_save())

    async def _start_engines_checked(self):
        """开启自动交易前先探测服务器连通性，未连接则取消切换并提示。"""
        if self._vm is None:
            return
        try:
            await check_server_health(self._vm.config.server_url)
        except Exception as e:
            self._toggle_rejected = True
            self.bootstrap.event_bus.publish(
                LogEvent(message=f"服务器未连接: {e}", level=LogLevel.ERROR)
            )
            self.auto_trade_rejected.emit()
            return
        self._handle_toggle_auto_trade(True)
        await self._start_engines()

    def _enabled_account_ids(self) -> list[str]:
        return [a.id for a in self.bootstrap.accounts if a.enabled]

    async def _start_engines(self):
        """启动全部已启用账户的引擎。单个账户失败不影响其余账户。"""
        started = False
        for account_id in self._enabled_account_ids():
            if account_id in self._engines and self._engines[account_id].is_running:
                continue
            try:
                engine = await self.bootstrap.build_engine(account_id)
                if self._vm is not None:
                    engine.set_auto_trade(self._vm.autoTrade)
                self._engines[account_id] = engine
                self._engine_tasks[account_id] = asyncio.create_task(engine.start())
                started = True
            except Exception as e:
                self.bootstrap.event_bus.publish(
                    LogEvent(
                        message=f"启动账户 {account_id} 失败: {e}", level=LogLevel.ERROR
                    )
                )
        if started:
            self.engine_started.emit()

    async def _stop_engines(self):
        """停止全部账户引擎。执行器由 shutdown 统一关闭。"""
        stopped = False
        for account_id, engine in list(self._engines.items()):
            try:
                await engine.stop()
                task = self._engine_tasks.get(account_id)
                if task is not None and not task.done():
                    try:
                        await asyncio.wait_for(task, timeout=5)
                    except Exception:
                        pass
                stopped = True
            except Exception as e:
                self.bootstrap.event_bus.publish(
                    LogEvent(
                        message=f"停止账户 {account_id} 失败: {e}", level=LogLevel.ERROR
                    )
                )
            finally:
                self._engines.pop(account_id, None)
                self._engine_tasks.pop(account_id, None)
        if stopped:
            self.engine_stopped.emit()

    @Slot()
    def do_quit(self):
        self.qt_app.quit()

    async def _shutdown(self):
        await self._stop_engines()
        await self.bootstrap.shutdown()
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        # _shutdown 运行在 asyncio 线程，QTimer.singleShot 的定时器没有事件循环可驱动，
        # 必须把退出动作排队到 UI 线程
        QMetaObject.invokeMethod(self, "do_quit", Qt.QueuedConnection)
