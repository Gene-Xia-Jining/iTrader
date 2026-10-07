# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_all

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

# 版本号唯一来源是 src/__init__.py（仅用于交叉确认，产物不单独记录版本）
sys.path.insert(0, ROOT)
from src import __version__ as VERSION  # noqa: E402,F401

# headless 后端（src/backend 入口）依赖树不含 Qt/presentation，全部排除；
# src 本体经 Analysis 收进 PYZ（生产布局无差量更新，无需外置）
binaries = []
hiddenimports = [
    'aiosqlite',
    'httpx',
    'pydantic',
    'cryptography',
]

# tqsdk 运行时必需数据（含 expired_quotes.json.lzma）。
# 过滤掉交互 Web 前端与示例：本客户端只走 TqApi/TargetPosTask 下单路径，
# 不启动 tqsdk 的 Web 服务，web/ 与 demo/ 永远不会被读取。
_tq_datas, tq_binaries, tq_hiddenimports = collect_all('tqsdk')
_drop = ('tqsdk/web', 'tqsdk/demo')
datas = [d for d in _tq_datas if not d[1].startswith(_drop)]
binaries += tq_binaries
hiddenimports += tq_hiddenimports

a = Analysis(
    [os.path.join(SPECPATH, 'backend_entry.py')],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(SPECPATH, 'runtime_hook.py')],
    excludes=[
        # UI 层依赖（旧 GUI 版专属），headless 后端不导入
        'PySide6',
        'shiboken6',
        # tqsdk/tafunc.py 顶层 `from scipy import stats`，但 stats 仅被期权定价
        # 私有函数使用，客户端不会触发；由 runtime_hook.py 提供等价 stub
        'scipy',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='backend',
)
