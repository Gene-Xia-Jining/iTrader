# iTrader — Extractable Components

> 源组件为 PySide6/Python 类，转换为 Petite-Vue HTML 模板时以浅色主题 QSS 规格为基准。

## Sidebar
- Source: `src/presentation/main_window.py`（`_build_ui` 中 sidebar 段）+ `src/presentation/components.py::SidebarButton`
- Category: layout
- Description: 240px 白色左侧导航，5 项（仪表盘 / Token 管理 / 交易日志 / 交易账号 / 设置），顶部无 logo（品牌在 head 条），选中项浅灰底胶囊描边。
- Extractable props: `activeItem` (string, default: "dashboard"), `items` (固定 5 项中文文案)
- Hardcoded: 240px 宽、#ffffff 底、右边框 #f0f0f0、44px 项高、8px 圆角选中态

## AppHeader (head 条)
- Source: `src/presentation/main_window.py::_build_ui` head 段
- Category: layout
- Description: parchment 底顶栏，左侧品牌两行（iTrader / 智能交易客户端），右侧「自动交易：开/关」状态按钮、「浅色/深色」主题按钮、「退出」危险按钮。
- Extractable props: `tradingActive` (boolean, default: false), `dark` (boolean, default: false)
- Hardcoded: 品牌文案、22px/600 标题、胶囊按钮组

## PageHeader
- Source: `src/presentation/components.py`
- Category: basic
- Description: 页面标题 22px/600 + 副标题 15px muted。
- Extractable props: `title` (string), `subtitle` (string)
- Hardcoded: 字号字重、颜色 token

## StatusPill
- Source: `src/presentation/components.py`
- Category: basic
- Description: pearl 底 hairline 描边全圆角胶囊，内含 10px 语义色圆点 + 600 字重状态文字。
- Extractable props: `statusText` (string, default: "未连接"), `statusColor` (string, default: "#e74c3c")
- Hardcoded: 12/8 内边距、10px 圆点

## Card
- Source: `src/presentation/components.py`
- Category: basic
- Description: 白底 1px hairline 18px 圆角卡片容器。
- Extractable props: 无（纯容器）
- Hardcoded: 全部视觉规格

## ServerUrlTestRow
- Source: `src/presentation/pages.py`
- Category: basic
- Description: 「?」圆形帮助钮 + URL 输入框（占位 http://localhost:8000）+「测试连接」secondary 钮 + 可显隐结果行。
- Extractable props: `value` (string, default: "http://localhost:8000"), `resultText` (string), `resultState` ("success"|"error"|"pending"|null)
- Hardcoded: 20px 圆形 ? 钮、按钮文案
