# iTrader — App Shell / Layout (PySide6 QMainWindow)

> 主窗口 1180×760（最小 960×620）。结构：自定义顶部 head 条 + 左侧 sidebar(240px) + 右侧页面 QStackedWidget + 底部状态栏。macOS 上 QMenuBar 由系统菜单栏承载，窗口内不渲染。

## MainWindow._build_ui — 完整渲染代码

```python
def _build_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    head = QFrame()
    head.setObjectName("head")
    head_layout = QHBoxLayout(head)
    head_layout.setContentsMargins(20, 14, 20, 14)
    head_layout.setSpacing(12)
    brand = QVBoxLayout()
    brand.setSpacing(2)
    brand_label = QLabel("iTrader", head)
    brand_label.setObjectName("title")          # 22px / 600 / -0.4px
    brand_sub = QLabel("智能交易客户端", head)
    brand_sub.setObjectName("subtitle")          # 15px muted
    brand.addWidget(brand_label)
    brand.addWidget(brand_sub)
    head_layout.addLayout(brand)
    head_layout.addStretch(1)
    self._head_auto_btn = make_button("", variant="")   # 文案运行时设为「自动交易：开/关」，variant 在 success/secondary 间切换
    self._head_auto_btn.setToolTip("点击启动/停止自动交易")
    head_layout.addWidget(self._head_auto_btn)
    self._head_theme_btn = make_button("", variant="secondary")  # 文案「浅色/深色」
    self._head_theme_btn.setCheckable(True)
    head_layout.addWidget(self._head_theme_btn)
    self._head_quit_btn = make_button("退出", variant="danger")
    head_layout.addWidget(self._head_quit_btn)
    layout.addWidget(head)

    body = QWidget()
    body_layout = QHBoxLayout(body)
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(0)

    sidebar = QFrame()
    sidebar.setObjectName("sidebar")
    sidebar.setFixedWidth(240)
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(14, 18, 14, 18)
    sidebar_layout.setSpacing(10)

    nav = QVBoxLayout()
    nav.setSpacing(6)
    self.dashboard_btn = SidebarButton("仪表盘", sidebar)
    self.token_btn = SidebarButton("Token 管理", sidebar)
    self.log_btn = SidebarButton("交易日志", sidebar)
    self.account_btn = SidebarButton("交易账号", sidebar)
    self.settings_btn = SidebarButton("设置", sidebar)
    for button in (self.dashboard_btn, self.token_btn, self.log_btn, self.account_btn, self.settings_btn):
        nav.addWidget(button)
    self.dashboard_btn.setChecked(True)
    sidebar_layout.addLayout(nav)
    sidebar_layout.addStretch(1)

    self.stack = QStackedWidget()
    self.dashboard_page = DashboardPage()
    self.token_page = TokenPage()
    self.log_page = LogPage()
    self.account_page = AccountPage()
    self.settings_page = SettingsPage()
    for page in (self.dashboard_page, self.token_page, self.log_page, self.account_page, self.settings_page):
        self.stack.addWidget(page)
    self.stack.setCurrentIndex(0)

    body_layout.addWidget(sidebar)
    body_layout.addWidget(self.stack, 1)
    layout.addWidget(body, 1)

def _build_statusbar(self):
    bar = self.statusBar()
    self._status_text = QLabel("就绪")
    bar.addWidget(self._status_text, 1)
```

## 视觉规格（浅色主题，默认）
- **head**：parchment `#f5f5f7` 背景（继承 QWidget），内边距 20/14；左侧品牌两行，右侧 3 个胶囊按钮（自动交易：关 = secondary ghost 蓝字；深色 = secondary；退出 = danger 红 `#e3342f` 白字）。所有按钮 9999px 胶囊、min-height 36px、padding 10px 22px、600 字重。
- **sidebar**：白色 `#ffffff`，固定 240px，右边框 1px `#f0f0f0`；内边距 14/18；导航项间距 6，高 44px，左对齐文字，选中项 `#f0f0f0` 底 + 1px `#e0e0e0` 边框 + 8px 圆角，未选中灰字 `#7a7a7a`。
- **内容区**：parchment `#f5f5f7`，页面内边距 24。
- **状态栏**：白底（QStatusBar `#ffffff`）+ 顶边框 1px `#f0f0f0`，左侧「就绪」灰字 `#7a7a7a`。
- 深色主题对应：head/sidebar 变 tile `#252527`，内容区 `#272729`，强调色换 Sky Link Blue `#2997ff`。
