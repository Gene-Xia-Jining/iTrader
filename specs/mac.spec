# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

datas = [
    (os.path.join(ROOT, 'config.toml'), '.'),
]
binaries = []
hiddenimports = [
    # legacy flat modules (still shipped for backward compat)
    'db',
    'server',
    'trader',
    'models',
    'config',
    'app',
    'main',
    'token_manager',
    'cert_enroll',
    'pki_client',
    'main_with_cert',
    'run_app',
    # clean-architecture itrader package
    'itrader',
    *collect_submodules('itrader'),
    # deps
    'aiosqlite',
    'httpx',
    'pydantic',
    'toml',
    'tomllib',
    'cryptography',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'shiboken6',
]

# tqsdk 包含运行时必需的数据文件（web 页面等），需一并收集
tq_datas, tq_binaries, tq_hiddenimports = collect_all('tqsdk')
datas += tq_datas
binaries += tq_binaries
hiddenimports += tq_hiddenimports

# pyside6 plugins / QML data
ps_datas, ps_binaries, ps_hiddenimports = collect_all('PySide6')
datas += ps_datas
binaries += ps_binaries
hiddenimports += ps_hiddenimports

a = Analysis(
    [os.path.join(SRC, 'run_app.py')],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ],
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
    info_plist={
        'CFBundleDevelopmentRegion': 'zh_CN',
        'CFBundleAllowMixedLocalizations': True,
        'CFBundleLocalizations': ['zh_CN', 'en'],
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)
