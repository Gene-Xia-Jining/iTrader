# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

a = Analysis(
    [os.path.join(SRC, 'tray.py')],
    pathex=[SRC],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'config.toml'), '.'),
    ],
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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='iTrader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)