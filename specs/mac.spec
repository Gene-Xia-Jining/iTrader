# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

datas = [
    (os.path.join(ROOT, 'config.toml'), '.'),
]
binaries = []
hiddenimports = [
    'db',
    'server',
    'trader',
    'models',
    'config',
    'app',
    'main',
    'aiosqlite',
    'httpx',
    'pydantic',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'toml',
    'tomllib',
]

# tqsdk 包含运行时必需的数据文件（web 页面等），需一并收集
tq_datas, tq_binaries, tq_hiddenimports = collect_all('tqsdk')
datas += tq_datas
binaries += tq_binaries
hiddenimports += tq_hiddenimports

a = Analysis(
    [os.path.join(SRC, 'tray.py')],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='iTrader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='iTrader.app',
    bundle_identifier='com.xiajining.itrader',
)
