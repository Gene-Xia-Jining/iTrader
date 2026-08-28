# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

datas = [
    ('config.toml', '.'),
]

a = Analysis(
    ['tray_app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
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
        'tqsdk',
    ],
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