import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import sys
from pathlib import Path
import tomllib
import json
from datetime import datetime

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("iTrader 交易客户端")
        self.root.geometry("800x600")
        
        # 应用程序状态
        self.trading_active = False
        self.trading_thread = None
        self.loop = None
        
        # 配置
        self.config = self.load_config()
        
        # 创建界面
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        # 设置关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """加载配置文件"""
        config_path = Path("config.toml")
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                messagebox.showerror("配置错误", f"配置文件加载失败: {e}")
                return {}
        return {
            "server_url": "http://localhost:8000",
            "symbols": ["SA2409"],
            "auto_trade": False,
            "tq_account": "",
            "tq_password": "",
            "initial_balance": 10000000
        }
    
    def create_menu(self):
        """创建菜单栏（覆盖 macOS 默认的英文 File/Edit/Window/Help）"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单（替换英文 File）
        file_menu = tk.Menu(menubar, tearoff=0)
        if sys.platform == "darwin":
            file_menu.add_command(label="关闭窗口", accelerator="Cmd+W",
                                  command=lambda: self.root.event_generate("<<CloseWindow>>"))
        file_menu.add_command(label="配置设置", command=self.open_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", accelerator="Cmd+Q" if sys.platform == "darwin" else "Ctrl+Q",
                              command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 编辑菜单（替换英文 Edit）
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="撤销", accelerator="Cmd+Z" if sys.platform == "darwin" else "Ctrl+Z",
                              command=lambda: self.root.event_generate("<<Undo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", accelerator="Cmd+X" if sys.platform == "darwin" else "Ctrl+X",
                              command=lambda: self.root.event_generate("<<Cut>>"))
        edit_menu.add_command(label="复制", accelerator="Cmd+C" if sys.platform == "darwin" else "Ctrl+C",
                              command=lambda: self.root.event_generate("<<Copy>>"))
        edit_menu.add_command(label="粘贴", accelerator="Cmd+V" if sys.platform == "darwin" else "Ctrl+V",
                              command=lambda: self.root.event_generate("<<Paste>>"))
        edit_menu.add_command(label="全选", accelerator="Cmd+A" if sys.platform == "darwin" else "Ctrl+A",
                              command=lambda: self.root.event_generate("<<SelectAll>>"))
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 交易菜单
        trading_menu = tk.Menu(menubar, tearoff=0)
        trading_menu.add_command(label="启动自动交易", command=self.start_trading)
        trading_menu.add_command(label="停止自动交易", command=self.stop_trading)
        menubar.add_cascade(label="交易", menu=trading_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="清空日志", command=self.clear_logs)
        menubar.add_cascade(label="视图", menu=view_menu)

        # 窗口菜单（替换英文 Window）
        window_menu = tk.Menu(menubar, tearoff=0)
        if sys.platform == "darwin":
            window_menu.add_command(label="最小化", accelerator="Cmd+M",
                                    command=lambda: self.root.iconify())
            window_menu.add_command(label="缩放",
                                    command=lambda: self.root.event_generate("<<Zoom>>"))
            window_menu.add_separator()
        window_menu.add_command(label="显示主窗口",
                                command=lambda: (self.root.deiconify(), self.root.lift(), self.root.focus_force()))
        menubar.add_cascade(label="窗口", menu=window_menu)
        
        # 帮助菜单（替换英文 Help）
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明")
        help_menu.add_command(label="关于",
                              command=lambda: messagebox.showinfo(
                                  "关于", "iTrader 交易客户端\n版本 0.1.0", parent=self.root))
        menubar.add_cascade(label="帮助", menu=help_menu)
    
    def create_main_frame(self):
        """创建主界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左侧控制面板
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
        
        # 分割线
        ttk.Separator(control_frame, orient="horizontal").grid(row=4, column=0, columnspan=2, 
                                                              sticky=(tk.W, tk.E), pady=10)
        
        # 快速设置
        ttk.Label(control_frame, text="自动交易:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.auto_trade_var = tk.BooleanVar(value=self.config.get("auto_trade", False))
        ttk.Checkbutton(control_frame, variable=self.auto_trade_var, 
                       command=self.toggle_auto_trade).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # 右侧日志面板
        log_frame = ttk.LabelFrame(main_frame, text="交易日志", padding="10")
        log_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=60, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行权重
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.count_var = tk.StringVar(value="交易记录: 0")
        count_label = ttk.Label(status_frame, textvariable=self.count_var, anchor=tk.E)
        count_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        status_frame.columnconfigure(0, weight=3)
        status_frame.columnconfigure(1, weight=1)
    
    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
        # 更新状态栏
        self.root.after(0, self.update_status, f"日志: {message}")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def start_trading(self):
        """启动自动交易"""
        if self.trading_active:
            return
            
        self.trading_active = True
        self.trading_status_var.set("运行中")
        self.trading_status_var.set("运行中")
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 启动交易线程
        self.loop = asyncio.new_event_loop()
        self.trading_thread = threading.Thread(target=self.run_trading, daemon=True)
        self.trading_thread.start()
        
        self.log_message("自动交易已启动")
    
    async def trading_loop(self):
        """交易主循环"""
        # 导入交易模块
        from database import Database
        from server import ServerClient
        from trader import Trader
        
        try:
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
            
            self.root.after(0, self.server_status_var.set, "已连接")
            self.log_message(f"连接到服务器: {self.config['server_url']}")
            
            while self.trading_active:
                try:
                    async for result in server.stream():
                        if not self.trading_active:
                            break
                            
                        message = f"收到策略结果: {result.symbol} 价位 {result.price} 仓位 {result.position}"
                        self.root.after(0, self.log_message, message)
                        
                        # 幂等检查
                        if await db.exists(result.id):
                            self.root.after(0, self.log_message, f"已执行过: {result.id}", "WARNING")
                            continue
                        
                        # 落库
                        await db.insert_pending(result)
                        
                        # 自动交易检查
                        if not self.config.get("auto_trade", False):
                            self.root.after(0, self.log_message, "自动交易关闭", "INFO")
                            continue
                        
                        try:
                            # 执行交易
                            await trader.execute(result.symbol, result.position)
                            
                            # 更新数据库状态
                            await db.set_executed(result.id)
                            
                            success_msg = f"交易执行成功: {result.symbol} 仓位 {result.position}"
                            self.root.after(0, self.log_message, success_msg, "SUCCESS")
                            
                        except Exception as e:
                            error_msg = f"交易执行失败: {str(e)}"
                            await db.set_failed(result.id, str(e))
                            self.root.after(0, self.log_message, error_msg, "ERROR")
                            
                except Exception as e:
                    if self.trading_active:
                        error_msg = f"连接错误: {str(e)}"
                        self.root.after(0, self.log_message, error_msg, "ERROR")
                        await asyncio.sleep(5)  # 等待后重试
            
        except Exception as e:
            if self.trading_active:
                error_msg = f"交易系统错误: {str(e)}"
                self.root.after(0, self.log_message, error_msg, "ERROR")
        
        finally:
            self.root.after(0, self.stop_trading)
    
    def run_trading(self):
        """运行交易循环的线程函数"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.trading_loop())
        finally:
            self.loop.close()
    
    def stop_trading(self):
        """停止自动交易"""
        if not self.trading_active:
            return
            
        self.trading_active = False
        self.trading_status_var.set("已停止")
        self.trading_status_var.set("已停止")
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.log_message("自动交易已停止")
    
    def toggle_auto_trade(self):
        """切换自动交易开关"""
        auto_trade = self.auto_trade_var.get()
        self.config["auto_trade"] = auto_trade
        
        status = "开启" if auto_trade else "关闭"
        self.log_message(f"自动交易 {status}")
    
    def open_config(self):
        """打开配置窗口"""
        self.log_message("打开配置设置")
        # 这里可以创建配置对话框
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("日志已清空")
    
    def on_closing(self):
        """窗口关闭处理"""
        if self.trading_active:
            if messagebox.askyesno("确认退出", "自动交易正在运行，确定要退出吗？"):
                self.stop_trading()
                self.root.quit()
        else:
            self.root.quit()

def main():
    root = tk.Tk()
    app = TradingApp(root)
    
    # 设置窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()