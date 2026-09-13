#!/usr/bin/env python3
"""创建包含虚拟环境的iTrader Mac应用包"""

import os
import sys
import shutil
import subprocess
import venv
from pathlib import Path

def create_virtualenv():
    """创建虚拟环境"""
    print("创建虚拟环境...")
    venv_dir = Path("dist-mac/venv")
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
    
    # 创建虚拟环境
    venv.create(venv_dir, with_pip=True)
    print(f"✅ 虚拟环境创建成功: {venv_dir}")
    
    # 获取虚拟环境的Python路径
    if sys.platform == "darwin":
        python_path = venv_dir / "bin" / "python"
    else:
        python_path = venv_dir / "Scripts" / "python.exe"
    
    return str(python_path)

def install_dependencies(venv_python):
    """安装依赖到虚拟环境"""
    print("安装依赖...")
    
    # 依赖列表
    deps = [
        "PySide6>=6.6",
        "httpx", 
        "aiosqlite",
        "pydantic>=2.0",
        "tqsdk",
        "toml"
    ]
    
    # 安装依赖
    for dep in deps:
        print(f"安装 {dep}...")
        cmd = [venv_python, "-m", "pip", "install", dep]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {dep} 安装失败: {e}")
            continue
    
    print("✅ 依赖安装完成")

def create_app_bundle():
    """创建应用包"""
    print("创建应用包...")
    
    # 创建应用目录结构
    app_dir = Path("dist-mac/iTrader.app")
    if app_dir.exists():
        shutil.rmtree(app_dir)
    
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
    
    # Frameworks目录
    frameworks_dir = contents_dir / "Frameworks"
    frameworks_dir.mkdir(exist_ok=True)
    
    # 复制虚拟环境
    venv_dir = Path("dist-mac/venv")
    if venv_dir.exists():
        shutil.copytree(venv_dir, frameworks_dir / "venv", dirs_exist_ok=True)
        print("✅ 虚拟环境已复制到应用包")
    
    # 复制源代码
    src_dir = Path("src")
    if src_dir.exists():
        shutil.copytree(src_dir, app_dir / "Contents" / "src", dirs_exist_ok=True)
        print("✅ 源代码已复制到应用包")
    
    # 复制资源文件
    resources_src = Path("src/resources")
    if resources_src.exists():
        resources_dst = resources_dir / "resources"
        shutil.copytree(resources_src, resources_dst, dirs_exist_ok=True)
        print("✅ 资源文件已复制到应用包")
    
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
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>''')
    
    # 创建启动脚本
    launcher = macos_dir / "iTrader"
    launcher.write_text('''#!/bin/bash
# iTrader启动脚本

APP_DIR="$(dirname "$0")"
cd "$APP_DIR/.."

# 设置虚拟环境路径
VENV_PATH="$APP_DIR/../Frameworks/venv/bin/python"

# 检查虚拟环境是否存在
if [ ! -f "$VENV_PATH" ]; then
    echo "错误: 虚拟环境不存在"
    exit 1
fi

# 设置工作目录
WORKDIR="$HOME/.itrader"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# 运行应用
"$VENV_PATH" -c "
import sys
import os
sys.path.insert(0, '$APP_DIR/../src')

try:
    from __main__ import run_gui
    run_gui()
except KeyboardInterrupt:
    print('程序被用户中断')
except Exception as e:
    print(f'程序运行出错: {e}')
    input('按回车键退出...')
"''')
    
    # 设置执行权限
    launcher.chmod(0o755)
    
    # 复制图标文件
    icon_src = Path("src/resources/icon.png")
    if icon_src.exists():
        icon_dst = resources_dir / "icon.png"
        shutil.copy2(icon_src, icon_dst)
        print(f"✅ 图标已复制: {icon_dst}")
    
    print(f"✅ 应用包创建成功: {app_dir.absolute()}")
    print(f"📦 应用大小: {app_dir.stat().st_size / 1024 / 1024:.1f} MB")
    
    return app_dir

def main():
    """主函数"""
    print("=" * 60)
    print("iTrader Mac App 完整打包工具")
    print("=" * 60)
    
    # 检查当前目录
    if not Path("pyproject.toml").exists():
        print("❌ 错误: 请在iTrader项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    try:
        # 创建虚拟环境
        venv_python = create_virtualenv()
        
        # 安装依赖
        install_dependencies(venv_python)
        
        # 创建应用包
        app_path = create_app_bundle()
        
        print("\n🎉 打包完成!")
        print("📂 输出目录: dist-mac/")
        print("💡 使用方法: 双击 iTrader.app 运行")
        print("📱 应用将显示在菜单栏中")
        
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
