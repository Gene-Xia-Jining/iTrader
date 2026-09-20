# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

# src 整目录作为数据外置（不打进 PYZ）：补丁更新只需替换该目录；
# 排除 __pycache__ 避免把开发态缓存打进包。
# Tree 项为 (dest, src, kind) 且 dest 是完整文件路径；Analysis 的 datas
# 语义是 (源文件, 目标目录)，故取 dest 的目录部分
datas = [
    (src, os.path.dirname(dest))
    for dest, src, _kind in Tree(SRC, prefix='src', excludes=['*__pycache__*', '*.pyc'])
]
binaries = []
hiddenimports = [
    # deps（src 由上面 datas 外置，运行时经 runtime_hook 加入的路径加载）
    'aiosqlite',
    'httpx',
    'pydantic',
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

a = Analysis(
    [os.path.join(SRC, 'run_app.py')],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(SPECPATH, 'runtime_hook.py')],
    excludes=[
        # 应用只使用 QtCore / QtGui / QtWidgets，其余 Qt 模块全部排除
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtGraphs',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtXml',
        # tqsdk/tafunc.py 顶层 `from scipy import stats`，但 stats 仅被期权定价
        # 私有函数使用，客户端不会触发；由 runtime_hook.py 提供等价 stub
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
)

# onedir 产物 dist/iTrader/（顶层 iTrader.exe + _internal/）：
# 自动更新按程序目录整体替换，也支持替换 _internal/src 完成差量更新
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='iTrader',
)