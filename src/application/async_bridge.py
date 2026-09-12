import asyncio
import sys
import os
from pathlib import Path
from typing import Callable, Any


class AsyncQtBridge:
    """Bridges asyncio and Qt event loops using qasync or a polling approach."""

    def __init__(self, qt_app):
        self.qt_app = qt_app
        self._loop: asyncio.AbstractEventLoop | None = None

    def start_loop(self) -> asyncio.AbstractEventLoop:
        """Start asyncio loop that will drive Qt via QTimer polling."""
        if self._loop is not None and self._loop.is_running():
            return self._loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        return loop

    def stop_loop(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    @property
    def loop(self) -> asyncio.AbstractEventLoop | None:
        return self._loop

    def run_on_ui(self, fn: Callable[..., Any], *args, **kwargs):
        """Schedule callable to run on Qt UI thread."""
        try:
            from PySide6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self.qt_app,
                lambda: fn(*args, **kwargs),
                Qt.QueuedConnection,
            )
        except Exception:
            fn(*args, **kwargs)


def prepare_workdir() -> Path:
    """Switch to user-writable directory when frozen (PyInstaller)."""
    if getattr(sys, "frozen", False):
        workdir = Path.home() / ".itrader"
        workdir.mkdir(parents=True, exist_ok=True)
        os.chdir(workdir)
        Path("data").mkdir(parents=True, exist_ok=True)
        return workdir
    Path("data").mkdir(parents=True, exist_ok=True)
    return Path.cwd()
