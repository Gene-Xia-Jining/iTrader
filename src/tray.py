import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import asyncio
import threading
import pystray
from PIL import Image, ImageDraw
import sys
import os
from pathlib import Path
import tomllib
import json
from datetime import datetime


class ConfigDialog(tk.Toplevel):
    """配置对话框"""

    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("配置设置")
        self.config_data = config.copy()
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.center_window(500, 450)
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        row = 0
        
        # 服务器地址
        ttk.Label(main_frame, text="服务器地址:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.server_url_var = tk.StringVar(value=self.config_data.get("server_url", ""))
        ttk.Entry(main_frame, textvariable=self.server_url_var, width=30).grid(row=row, column=1, pady=5)
        row += 1
        
        # 天勤账号
        ttk.Label(main_frame, text="天勤账号:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tq_account_var = tk.StringVar(value=self.config_data.get("tq_account", ""))
        ttk.Entry(main_frame, textvariable=self.tq_account_var, width=30).grid(row=row, column=1, pady=5)
        row += 1
        
        # 天勤密码
        ttk.Label(main_frame, text="天勤密码:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tq_password_var = tk.StringVar(value=self.config_data.get("tq_password", ""))
        ttk.Entry(main_frame, textvariable=self.tq_password_var, width=30, show="*").grid(row=row, column=1, pady=5)
        row += 1
        
        # 初始资金
        ttk.Label(main_frame, text="初始资金:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.initial_balance_var = tk.StringVar(value=str(self.config_data.get("initial_balance", 10000000)))
        ttk.Entry(main_frame, textvariable=self.initial_balance_var, width=30).grid(row=row, column=1, pady=5)
        row += 1
        
        # 交易品种
        ttk.Label(main_frame, text="交易品种:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.symbols_var = tk.StringVar(value=",".join(self.config_data.get("symbols", [])))
        ttk.Entry(main_frame, textvariable=self.symbols_var, width=30).grid(row=row, column=1, pady=5)
        ttk.Label(main_frame, text="(逗号分隔)", foreground="gray").grid(row=row, column=2, pady=5)
        row += 1
        
        # 自动交易
        self.auto_trade_var = tk.BooleanVar(value=self.config_data.get("auto_trade", False))
        ttk.Checkbutton(main_frame, text="自动交易", variable=self.auto_trade_var).grid(row=row, column=0, pady=5)
        row += 1
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="确定", command=self.on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.on_cancel, width=10).pack(side=tk.LEFT, padx=5)
    
    def on_ok(self):
        """确定按钮"""
        try:
            self.result = {
                "server_url": self.server_url_var.get(),
                "tq_account": self.tq_account_var.get(),
                "tq_password": self.tq_password_var.get(),
                "initial_balance": float(self.initial_balance_var.get()),
                "symbols": [s.strip() for s in self.symbols_var.get().split(",") if s.strip()],
                "auto_trade": self.auto_trade_var.get()
            }
            self.destroy()
        except ValueError as e:
            messagebox.showerror("输入错误", f"请检查输入: {e}", parent=self)
    
    def on_cancel(self):
        """取消按钮"""
        self.destroy()
    
    def center_window(self, width, height):
        """居中显示窗口"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')


class TradingTrayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        
        # 应用程序状态
        self.trading_active = False
        self.trading_thread = None
        self.loop = None
        self.tray_icon = None
        
        # 配置
        self.config = self.load_config()
        
        # 创建托盘图标
        self.create_tray_icon()
        
        # 创建主窗口
        self.create_main_window()
    
    def load_config(self):
        """加载配置文件"""
        config_path = Path("config.toml")
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                self.show_error(f"配置文件加载失败: {e}")
                return {}
        return {
            "server_url": "http://localhost:8000",
            "symbols": ["SA2409"],
            "auto_trade": False,
            "tq_account": "",
            "tq_password": "",
            "initial_balance": 10000000
        }
    
    def create_image(self, width, height, color1, color2):
        """创建托盘图标图像"""
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
            fill=color2
        )
        return image
    
    def create_tray_icon(self):
        """创建托盘图标"""
        # 创建图标图像
        icon_image = self.create_image(64, 64, 'darkblue', 'yellow')
        
        # 创建托盘菜单
        menu = (
            pystray.MenuItem("显示/隐藏主窗口", self.toggle_main_window),
            pystray.MenuItem("启动自动交易", self.start_trading),
            pystray.MenuItem("停止自动交易", self.stop_trading),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("配置设置", self.open_config_window),
            pystray.MenuItem("查看日志", self.show_log_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit_app)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "iTrader",
            icon_image,
            "iTrader 交易客户端",
            menu
        )
        
        # 在单独的线程中运行托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_main_window(self):
        """创建主窗口"""
        self.main_window = tk.Toplevel(self.root)
        self.main_window.title("iTrader 交易客户端")
        self.main_window.geometry("800x600")
        self.main_window.protocol("WM_DELETE_WINDOW", self.hide_main_window)
        
        # 创建界面
        self.create_main_frame()
        self.create_status_bar()
        
        # 初始隐藏
        self.hide_main_window()
    
    def create_main_frame(self):
        """创建主界面"""
        main_frame = ttk.Frame(self.main_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 服务器状态
        self.server_status_var = tk.StringVar(value="未连接")
        ttk.Label(control_frame, text="服务器状态:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(control_frame, textvariable=self.server_status_var, 
                  foreground="red").grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 交易状态
        self.trading_status_var = tk.StringVar(value="已停止")
        ttk.Label(control_frame, text="交易状态:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(control_frame, textvariable=self.trading_status_var, 
                  foreground="red").grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 控制按钮
        self.start_btn = ttk.Button(control_frame, text="启动自动交易", 
                                    command=self.start_trading, width=15)
        self.start_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.stop_btn = ttk.Button(control_frame, text="停止自动交易", 
                                   command=self.stop_trading, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 自动交易开关
        ttk.Label(control_frame, text="自动交易:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.auto_trade_var = tk.BooleanVar(value=self.config.get("auto_trade", False))
        ttk.Checkbutton(control_frame, variable=self.auto_trade_var, 
                       command=self.toggle_auto_trade).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 日志面板
        log_frame = ttk.LabelFrame(main_frame, text="交易日志", padding="10")
        log_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=60, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.main_window, relief=tk.SUNKEN)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        status_frame.columnconfigure(0, weight=1)
    
    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
        # 更新状态栏
        self.main_window.after(0, self.update_status, f"日志: {message}")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def toggle_main_window(self, icon=None, item=None):
        """显示/隐藏主窗口"""
        if self.main_window.winfo_viewable():
            self.hide_main_window()
        else:
            self.show_main_window()
    
    def show_main_window(self):
        """显示主窗口"""
        self.main_window.deiconify()
        self.main_window.lift()
        self.main_window.focus_force()
    
    def hide_main_window(self):
        """隐藏主窗口"""
        self.main_window.withdraw()
    
    def start_trading(self, icon=None, item=None):
        """启动自动交易"""
        if self.trading_active:
            return
            
        self.trading_active = True
        self.trading_status_var.set("运行中")
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 启动交易线程
        self.loop = asyncio.new_event_loop()
        self.trading_thread = threading.Thread(target=self.run_trading, daemon=True)
        self.trading_thread.start()
        
        self.log_message("自动交易已启动")
        self.show_notification("交易启动", "自动交易已启动")
    
    async def trading_loop(self):
        """交易主循环"""
        try:
            # 导入交易模块
            from db import Database
            from server import ServerClient
            from trader import Trader
            
            # 初始化数据库
            db = Database("data/client.db")
            await db.init()
            
            # 初始化交易器
            trader = Trader(
                account=self.config["tq_account"],
                password=self.config["tq_password"],
                initial_balance=self.config["initial_balance"],
            )
            
            # 初始化服务器客户端
            server = ServerClient(
                server_url=self.config["server_url"],
                symbols=self.config["symbols"],
            )
            
            self.main_window.after(0, self.server_status_var.set, "已连接")
            self.log_message(f"连接到服务器: {self.config['server_url']}")
            
            while self.trading_active:
                try:
                    async for result in server.stream():
                        if not self.trading_active:
                            break
                            
                        message = f"收到策略结果: {result.symbol} 价位 {result.price} 仓位 {result.position}"
                        self.main_window.after(0, self.log_message, message)
                        
                        # 幂等检查
                        if await db.exists(result.id):
                            self.main_window.after(0, self.log_message, f"已执行过: {result.id}", "WARNING")
                            continue
                        
                        # 落库
                        await db.insert_pending(result)
                        
                        # 自动交易检查
                        if not self.config.get("auto_trade", False):
                            self.main_window.after(0, self.log_message, "自动交易关闭", "INFO")
                            continue
                        
                        try:
                            # 执行交易
                            await trader.execute(result.symbol, result.position)
                            
                            # 更新数据库状态
                            await db.set_executed(result.id)
                            
                            success_msg = f"交易执行成功: {result.symbol} 仓位 {result.position}"
                            self.main_window.after(0, self.log_message, success_msg, "SUCCESS")
                            
                        except Exception as e:
                            error_msg = f"交易执行失败: {str(e)}"
                            await db.set_failed(result.id, str(e))
                            self.main_window.after(0, self.log_message, error_msg, "ERROR")
                            
                except Exception as e:
                    if self.trading_active:
                        error_msg = f"连接错误: {str(e)}"
                        self.main_window.after(0, self.log_message, error_msg, "ERROR")
                        await asyncio.sleep(5)
            
        except Exception as e:
            if self.trading_active:
                error_msg = f"交易系统错误: {str(e)}"
                self.main_window.after(0, self.log_message, error_msg, "ERROR")
        
        finally:
            self.main_window.after(0, self.stop_trading)
    
    def run_trading(self):
        """运行交易循环的线程函数"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.trading_loop())
        finally:
            self.loop.close()
    
    def stop_trading(self, icon=None, item=None):
        """停止自动交易"""
        if not self.trading_active:
            return
            
        self.trading_active = False
        self.trading_status_var.set("已停止")
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.log_message("自动交易已停止")
        self.show_notification("交易停止", "自动交易已停止")
    
    def toggle_auto_trade(self):
        """切换自动交易开关"""
        auto_trade = self.auto_trade_var.get()
        self.config["auto_trade"] = auto_trade
        
        status = "开启" if auto_trade else "关闭"
        self.log_message(f"自动交易 {status}")
    
    def open_config_window(self, icon=None, item=None):
        """打开配置窗口"""
        self.show_main_window()
        
        dialog = ConfigDialog(self.main_window, self.config)
        self.main_window.wait_window(dialog)
        
        if dialog.result:
            self.config.update(dialog.result)
            self.save_config()
            self.auto_trade_var.set(self.config.get("auto_trade", False))
            self.log_message("配置已保存")
    
    def save_config(self):
        """保存配置文件"""
        try:
            import toml
            with open("config.toml", "w", encoding="utf-8") as f:
                toml.dump(self.config, f)
        except ImportError:
            messagebox.showerror("保存失败", "需要安装 toml 库: pip install toml")
    
    def show_log_window(self, icon=None, item=None):
        """显示日志窗口"""
        self.show_main_window()
        self.log_text.see(tk.END)
    
    def show_error(self, message):
        """显示错误消息"""
        self.main_window.after(0, messagebox.showerror, "错误", message)
    
    def show_notification(self, title, message):
        """显示系统通知"""
        if self.tray_icon:
            try:
                import platform
                if platform.system() == "Windows":
                    self.tray_icon.notify(message, title)
            except:
                pass
    
    def quit_app(self, icon=None, item=None):
        """退出应用程序"""
        if self.trading_active:
            if messagebox.askyesno("确认退出", "自动交易正在运行，确定要退出吗？"):
                self.stop_trading()
                if self.tray_icon:
                    self.tray_icon.stop()
                self.root.quit()
                sys.exit(0)
        else:
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
            sys.exit(0)
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

def main():
    app = TradingTrayApp()
    app.run()

if __name__ == "__main__":
    main()