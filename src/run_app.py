import importlib
import sys


def main():
    if getattr(sys, "frozen", False):
        # frozen 下 src 以外部目录随包分发（支持差量更新，见 specs/*.spec）；
        # 动态导入避免 PyInstaller 静态分析把 src 重新收进 PYZ
        importlib.import_module("src.__main__").run_gui()
    else:
        from src.__main__ import run_gui
        run_gui()


if __name__ == "__main__":
    main()
