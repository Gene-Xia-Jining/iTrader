"""PyInstaller 入口：等价于 `python -m src.backend`。

src/backend/__main__.py 含包内相对导入（from .rpc import ...），不能作为
PyInstaller 顶层脚本静态分析；由这里以完整包路径导入后调用 main()。
"""

from src.backend.__main__ import main

if __name__ == "__main__":
    main()
