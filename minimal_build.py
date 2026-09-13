#!/usr/bin/env python3
"""最小化iTrader Mac App打包脚本"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """清理之前的构建文件"""
    build_dirs = ['build', 'dist', 'dist-mac']
    for dir_name in build_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"清理 {dir_name}")

def create_simple_app():
    """创建简化的应用包"""
    print("创建简化版iTrader应用...")
    
    # 清理之前的构建
    clean_build()
    
    # 创建应用目录结构
    app_dir = Path("dist-mac/iTrader.app")
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建Mac应用包结构
    contents_dir = app_dir / "Contents"
    contents_dir.mkdir(exist_ok=True)
    
    # MacOS目录
    macos_dir = contents_dir / "MacOS"
    macos_dir.mkdir(exist_ok=True)
    
    # Resources目录
    resources_dir = contents_dir / "Resources"
    resources_dir.mkdir(exist_ok=True)
    
    # 创建Info.plist文件
    info_plist = contents_dir / "Info.plist"
    info_plist.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>iTrader</string>
    <key>CFBundleIdentifier</key>
    <string>com.itradertool.app</string>
    <key>CFBundleName</key>
    <string>iTrader</string>
    <key>CFBundleVersion</key>
    <string>0.0.2</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>''')
    
    # 复制图标文件
    icon_src = Path("src/resources/icon.png")
    if icon_src.exists():
        icon_dst = resources_dir / "icon.png"
        shutil.copy2(icon_src, icon_dst)
        print(f"复制图标: {icon_src} -> {icon_dst}")
    
    # 创建启动脚本
    launcher = macos_dir / "iTrader"
    launcher.write_text('''#!/bin/bash
cd "$(dirname "$0")"
cd ../../..
python3 -c "
import sys
import os
from pathlib import Path

# 设置工作目录
workdir = Path.home() / '.itrader'
workdir.mkdir(parents=True, exist_ok=True)
os.chdir(workdir)

# 添加项目路径
sys.path.insert(0, str(Path('$(dirname "$0")").parent.parent.parent))

try:
    from src.__main__ import run_gui
    run_gui()
except KeyboardInterrupt:
    print('程序被用户中断')
except Exception as e:
    print(f'程序运行出错: {e}')
    input('按回车键退出...')
"''')
    
    # 设置执行权限
    launcher.chmod(0o755)
    
    print(f"✅ 应用包创建成功: {app_dir.absolute()}")
    print(f"📦 应用大小: {app_dir.stat().st_size / 1024 / 1024:.1f} MB")
    
    return app_dir

def main():
    """主函数"""
    print("=" * 50)
    print("iTrader Mac App 简化打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("pyproject.toml").exists():
        print("❌ 错误: 请在iTrader项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 创建应用包
    app_path = create_simple_app()
    
    print("\n🎉 打包完成!")
    print("📂 输出目录: dist-mac/")
    print("💡 使用方法: 双击 iTrader.app 中的可执行文件运行")
    print("⚠️  注意: 此版本需要系统安装所有Python依赖")

if __name__ == "__main__":
    main()
