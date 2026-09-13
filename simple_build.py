#!/usr/bin/env python3
"""简化的iTrader Mac App打包脚本"""

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

def build_app():
    """打包Mac应用"""
    print("开始打包iTrader Mac应用...")
    
    # 清理之前的构建
    clean_build()
    
    # 创建dist目录
    dist_dir = Path("dist-mac")
    dist_dir.mkdir(exist_ok=True)
    
    # PyInstaller命令 - 简化版本
    cmd = [
        'pyinstaller',
        '--name=iTrader',
        '--windowed',  # 无控制台窗口
        '--onefile',   # 单文件
        '--add-data=src/resources:resources',  # 包含资源文件
        '--icon=src/resources/icon.png',  # 图标
        '--workpath=build',
        '--distpath=dist-mac',
        'src/__main__.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ PyInstaller打包成功!")
        
        # 检查输出文件
        app_path = dist_dir / "iTrader.app"
        if app_path.exists():
            print(f"✅ 应用包创建成功: {app_path.absolute()}")
            print(f"📦 应用大小: {app_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print("❌ 应用包未找到")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller打包失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 打包异常: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("iTrader Mac App 打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("pyproject.toml").exists():
        print("❌ 错误: 请在iTrader项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller可用")
    except ImportError:
        print("❌ 错误: 缺少PyInstaller依赖")
        print("请运行: pip install pyinstaller")
        sys.exit(1)
    
    # 执行打包
    if build_app():
        print("\n🎉 打包完成!")
        print("📂 输出目录: dist-mac/")
        print("💡 使用方法: 双击 iTrader.app 即可运行")
    else:
        print("\n❌ 打包失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
