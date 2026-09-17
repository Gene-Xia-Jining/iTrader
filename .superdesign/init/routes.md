# iTrader — Page Mapping（Qt QStackedWidget，无 URL 路由）

| Index | 页面 | 类 | 文件 | 内容摘要 |
|---|---|---|---|---|
| 0 | 仪表盘 | `DashboardPage` | `src/presentation/pages.py` | 服务器状态卡 + 交易状态卡（各含 StatusPill）+ 快捷操作卡（配置设置 / Token 管理 / 清空日志） |
| 1 | Token 管理 | `TokenPage` | `src/presentation/pages.py` | PageHeader + 表单卡（申请说明输入框、审批状态标签）+ 申请 Token / 刷新状态 / 查看状态按钮 |
| 2 | 交易日志 | `LogPage` | `src/presentation/pages.py` | PageHeader + 工具行（清空日志按钮）+ 只读等宽日志视图（QTextEdit#logView，pearl 底 11px 圆角） |
| 3 | 交易账号 | `AccountPage` | `src/presentation/pages.py` | PageHeader + 表单卡（天勤账号 / 天勤密码 / 初始资金 / 交易品种）+ 保存按钮 |
| 4 | 设置 | `SettingsPage` | `src/presentation/pages.py` | PageHeader + 表单卡（ServerUrlTestRow：? 帮助 + 地址输入 + 测试连接）+ 保存按钮 |

- 导航：sidebar 五个 SidebarButton ↔ stack index 一一对应（`_switch_page`）。
- 另有模态对话框 `ConfigDialog`（配置设置：服务器地址行 + 天勤账号/密码 + 初始资金 + 交易品种 + OK/Cancel），由菜单「文件 → 配置设置」触发，日常配置已在设置/账号页内联。
- 初始状态文案：服务器状态「未连接」（红 `#e74c3c`）、交易状态「已停止」（红）、状态栏「就绪」。
