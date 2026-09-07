# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/tray.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('config.toml', '.'),
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