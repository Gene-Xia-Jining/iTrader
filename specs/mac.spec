# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all

# SPECPATH 是 PyInstaller 注入的 spec 文件所在目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

# 版本号唯一来源是 src/__init__.py
sys.path.insert(0, ROOT)
from src import __version__ as VERSION  # noqa: E402

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
    # 实际用到的 Qt 模块（QtCore / QtGui / QtWidgets / QtSvg）
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'shiboken6',
]

# tqsdk 运行时必需数据（含 expired_quotes.json.lzma）。
# 过滤掉交互 Web 前端与示例：本客户端只走 TqApi/TargetPosTask 下单路径，
# 不启动 tqsdk 的 Web 服务，web/ 与 demo/ 永远不会被读取。
_tq_datas, tq_binaries, tq_hiddenimports = collect_all('tqsdk')
_drop = ('tqsdk/web', 'tqsdk/demo')
tq_datas = [d for d in _tq_datas if not d[1].startswith(_drop)]
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
        # 应用只用 QtCore / QtGui / QtWidgets / QtSvg，其余全部排除以减小体积
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtAsyncio',
        'PySide6.QtBluetooth',
        'PySide6.QtCanvasPainter',
        'PySide6.QtCharts',
        'PySide6.QtConcurrent',
        'PySide6.QtDBus',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtHelp',
        'PySide6.QtHttpServer',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtNetworkAuth',
        'PySide6.QtNfc',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickTest',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtWebView',
        'PySide6.QtXml',
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
    version=VERSION,
    info_plist={
        'CFBundleDevelopmentRegion': 'zh_CN',
        'CFBundleAllowMixedLocalizations': True,
        'CFBundleLocalizations': ['zh_CN', 'en'],
        'NSHighResolutionCapable': True,
        'LSUIElement': True,
    },
)
