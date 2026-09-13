#!/usr/bin/env python3
"""iTrader Mac App打包脚本"""

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

def create_icns():
    """创建icns图标文件"""
    try:
        # 检查是否有iconutil
        if not shutil.which('iconutil'):
            print("警告: iconutil未找到，跳过icns创建")
            return None
            
        icon_png = Path("src/resources/icon.png")
        if not icon_png.exists():
            print("警告: icon.png不存在")
            return None
            
        # 创建临时目录
        temp_dir = Path("temp_icns")
        temp_dir.mkdir(exist_ok=True)
        
        # 复制图标到不同尺寸
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            temp_icon = temp_dir / f"icon_{size}x{size}.png"
            subprocess.run([
                'sips', '-z', str(size), str(size), str(icon_png), 
                '--out', str(temp_icon)
            ], check=True)
        
        # 创建icns文件
        icns_path = Path("dist/iTrader.icns")
        subprocess.run([
            'iconutil', '-c', 'icns', str(temp_dir), 
            '-o', str(icns_path)
        ], check=True)
        
        # 清理临时文件
        shutil.rmtree(temp_dir)
        
        print(f"创建图标: {icns_path}")
        return str(icns_path)
        
    except subprocess.CalledProcessError as e:
        print(f"创建图标失败: {e}")
        return None
    except Exception as e:
        print(f"创建图标异常: {e}")
        return None

def build_app():
    """打包Mac应用"""
    print("开始打包iTrader Mac应用...")
    
    # 清理之前的构建
    clean_build()
    
    # 创建dist目录
    dist_dir = Path("dist-mac")
    dist_dir.mkdir(exist_ok=True)
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--name=iTrader',
        '--windowed',  # 无控制台窗口
        '--onefile',   # 单文件
        '--add-data=src/resources:resources',  # 包含资源文件
        '--icon=src/resources/icon.png',  # 图标
        '--osx-bundle-identifier=com.itradertool.app',
        '--target-architecture=x86_64',  # 只支持Intel Mac
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
    
    # 检查依赖
    try:
        import PySide6
        print(f"✅ PySide6版本: {PySide6.__version__}")
    except ImportError:
        print("❌ 错误: 缺少PySide6依赖")
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
