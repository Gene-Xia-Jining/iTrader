# iTrader — Page Dependency Trees

## 0 仪表盘 DashboardPage
Entry: `src/presentation/pages.py::DashboardPage`
Dependencies:
- src/presentation/components.py
  - Card（QFrame#card）
  - StatusPill（QFrame#soft：圆点 + 状态文字）
  - PageHeader（仪表盘页未用 PageHeader，直接卡片网格）
- src/presentation/theme.py（DANGER/SUCCESS/WARNING、QSS）
- src/presentation/main_window.py（shell：head + sidebar + statusbar，见 layouts.md）

## 1 Token 管理 TokenPage
Entry: `src/presentation/pages.py::TokenPage`
Dependencies:
- src/presentation/components.py（Card、PageHeader）
- src/presentation/theme.py（WARNING 状态色）
- main_window.py（token_apply/refresh/status 按钮接线 + QMessageBox）

## 2 交易日志 LogPage
Entry: `src/presentation/pages.py::LogPage`
Dependencies:
- src/presentation/components.py（PageHeader）
- src/presentation/theme.py（MONO_FONT_FAMILY、logView QSS）
- main_window.py::_append_log（QTextCharFormat 按级别着色追加）

## 3 交易账号 AccountPage
Entry: `src/presentation/pages.py::AccountPage`
Dependencies:
- src/presentation/components.py（Card、PageHeader）
- src/presentation/theme.py（QSS 输入框/按钮）
- main_window.py（on_save 回调）

## 4 设置 SettingsPage
Entry: `src/presentation/pages.py::SettingsPage`
Dependencies:
- src/presentation/components.py（Card、PageHeader）
- src/presentation/pages.py::ServerUrlTestRow（? 帮助 + 输入 + 测试连接 + 结果标签）
- src/presentation/theme.py
- main_window.py（on_save / on_test 回调）

## 模态 ConfigDialog
Entry: `src/presentation/main_window.py::ConfigDialog`
Dependencies:
- ServerUrlTestRow + QFormLayout 表单（服务器地址 / 天勤账号 / 天勤密码 / 初始资金 / 交易品种 + 提示行）+ QDialogButtonBox(确定/取消)
