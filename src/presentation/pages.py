from typing import Optional, Callable
from PySide6.QtWidgets import QMessageBox

from PySide6.QtCore import Qt, QPoint, QRect, QSize, QByteArray
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLayoutItem,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..domain.entities import TradingConfiguration
from ..infrastructure.proxy import SYSTEM_PROXY
from .components import Card, PageHeader, StatusPill, StatusStatCard, ValueStatCard
from .theme import DANGER, MONO_FONT_FAMILY, SUCCESS, WARNING


def make_button(text: str, variant: str = "", style: str = "", object_name: str = ""):
    from PySide6.QtWidgets import QPushButton

    button = QPushButton(text)
    if variant:
        button.setProperty("variant", variant)
    if style:
        button.setStyleSheet(style)
    if object_name:
        button.setObjectName(object_name)
    return button


# Material Design 的 visibility / visibility_off 图标 path（Apache 2.0，24x24 viewBox）
_EYE_ON_PATH = (
    "M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5"
    "c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5"
    "-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
)
_EYE_OFF_PATH = (
    "M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92"
    "c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7"
    "l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46"
    "C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84"
    "l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55"
    "c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55"
    "c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2z"
    "m4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"
)


def _make_eye_icon(eye_off: bool, color: str = "#007aff") -> QIcon:
    """渲染密码可见性切换的睁眼/闭眼图标（单张 32x32 位图，不依赖系统字体）。

    #007aff 在明暗两主题下均可读（与页面链接色一致）。
    故意不用 devicePixelRatio=2 的位图：cocoa 真机上 QIcon 对 dpr 位图的
    尺寸匹配会放大裁切（offscreen 复现不出），单张 dpr=1 的 32px 位图配
    setIconSize(16,16) 在 Retina 下恰为 1:1 物理像素，普通屏为 2:1 下采样。
    """
    path = _EYE_OFF_PATH if eye_off else _EYE_ON_PATH
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<path fill="{color}" d="{path}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon


def make_divider() -> QFrame:
    """表单区与操作区之间的 1px 发丝分隔线，颜色随主题（QSS QFrame#divider）。"""
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    return line


class BasePage(QScrollArea):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setWidget(content)
        self.content_widget = content
        self.content_layout = layout

    def add_stretch(self):
        self.content_layout.addStretch(1)


class DashboardPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("仪表盘", "服务器连接与自动交易运行状态总览。")
        self.content_layout.addWidget(self.header)

        metrics = QGridLayout()
        metrics.setSpacing(16)
        self.server_status = StatusStatCard("服务器状态", "未配置服务器地址")
        metrics.addWidget(self.server_status, 0, 0)
        self.trade_status = StatusStatCard("交易状态", "自动交易未启动")
        metrics.addWidget(self.trade_status, 0, 1)
        self.balance_card = ValueStatCard("账户资金", "初始资金 (元)")
        metrics.addWidget(self.balance_card, 0, 2)
        self.symbols_card = ValueStatCard("活跃品种", "已订阅行情品种")
        metrics.addWidget(self.symbols_card, 0, 3)
        self.content_layout.addLayout(metrics)

        self.content_layout.addWidget(self._build_signal_card())
        self.content_layout.addWidget(self._build_log_card())

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.config_btn = make_button("配置设置", variant="secondary")
        self.token_btn = make_button("Token 管理", variant="secondary")
        actions.addWidget(self.config_btn)
        actions.addWidget(self.token_btn)
        actions.addStretch(1)
        self.content_layout.addLayout(actions)
        self.add_stretch()

    def _build_signal_card(self) -> Card:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        title = QLabel("最近信号", card)
        title.setObjectName("subtitle")
        layout.addWidget(title)
        empty = QLabel("暂无信号 — 服务器信号将在此显示", card)
        empty.setObjectName("dim")
        empty.setAlignment(Qt.AlignCenter)
        layout.addWidget(empty)
        return card

    def _build_log_card(self) -> Card:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("最近日志", card)
        title.setObjectName("subtitle")
        header.addWidget(title)
        header.addStretch(1)
        self.clear_logs_btn = make_button("清空日志", variant="flat")
        header.addWidget(self.clear_logs_btn)
        layout.addLayout(header)

        self.log_preview = QTextEdit(card)
        self.log_preview.setObjectName("logPreview")
        self.log_preview.setReadOnly(True)
        self.log_preview.document().setMaximumBlockCount(4)
        self.log_preview.document().setDocumentMargin(0)
        # 高度略大于 4 行行高之和，保证最新 4 条日志无需滚动即可全部可见
        self.log_preview.setFixedHeight(120)
        self.log_preview.setStyleSheet(
            "QTextEdit#logPreview { background: transparent; border: 0;"
            " font-family: %s; font-size: 12px; }" % MONO_FONT_FAMILY
        )
        layout.addWidget(self.log_preview)
        return card


class TokenPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("Token 管理", "申请、刷新并查看服务器审批状态。")
        self.content_layout.addWidget(self.header)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.token_description_edit = QLineEdit()
        self.token_description_edit.setPlaceholderText("例如：iTrader 智能交易系统")
        status_box = QWidget()
        # 容器 QWidget 会匹配全局窗口底色规则，白卡内需显式透明
        status_box.setStyleSheet("background: transparent;")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        self.token_status_label = QLabel("未申请")
        self.token_status_label.setObjectName("tokenStatus")
        self.token_status_label.setWordWrap(True)
        self.token_status_label.setStyleSheet("color: %s; background: transparent;" % WARNING)
        token_hint = QLabel("提交申请后等待服务器审批，可通过刷新状态查看进度")
        token_hint.setObjectName("dim")
        token_hint.setWordWrap(True)
        status_layout.addWidget(self.token_status_label)
        status_layout.addWidget(token_hint)
        form.addRow("申请说明:", self.token_description_edit)
        form.addRow("审批状态:", status_box)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.token_apply_btn = make_button("申请 Token")
        self.token_refresh_btn = make_button("刷新状态", variant="secondary")
        self.token_status_btn = make_button("查看状态", variant="secondary")
        self.token_status_btn.setEnabled(False)
        buttons.addWidget(self.token_apply_btn)
        buttons.addWidget(self.token_refresh_btn)
        buttons.addWidget(self.token_status_btn)
        buttons.addStretch(1)

        layout.addLayout(form)
        layout.addWidget(make_divider())
        layout.addLayout(buttons)
        self.content_layout.addWidget(card)
        self.add_stretch()


class LogPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("交易日志", "实时查看客户端连接、信号、下单和异常信息。")
        self.content_layout.addWidget(self.header)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        log_hint = QLabel("本地会话日志，保存在内存中")
        log_hint.setObjectName("dim")
        toolbar.addWidget(log_hint)
        toolbar.addStretch(1)
        self.clear_logs_btn = make_button("清空日志", variant="secondary")
        toolbar.addWidget(self.clear_logs_btn)
        self.content_layout.addLayout(toolbar)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "QTextEdit#logView { font-family: %s; font-size: 12px; }" % MONO_FONT_FAMILY
        )
        self.content_layout.addWidget(self.log_view, 1)


class SimulationPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._make_label(
            "在开始实盘交易之前，您应该通过 1-3 个月的模拟交易建立信心。<br><br>"
            "我们支持快期的模拟交易，您需要："
        ))

        layout.addWidget(self._make_label("1，下载快期模拟版客户端："))
        layout.addWidget(self._make_link_row(
            "手机端：", "https://www.shinnytech.com/products/app"
        ))
        # App Store 是手机端 iOS 渠道的子项，富文本中用 &nbsp; 缩进
        layout.addWidget(self._make_link_row(
            "&nbsp;&nbsp;&nbsp;&nbsp;App Store：",
            "https://itunes.apple.com/us/app/快期小q/id1187762307?l=zh&ls=1&mt=8",
        ))
        layout.addWidget(self._make_link_row(
            "Windows：", "https://www.shinnytech.com/products/q73"
        ))

        layout.addWidget(make_divider())

        layout.addWidget(self._make_label("2，在快期客户端或天勤官网注册："))
        layout.addWidget(self._make_link_row(
            "天勤官网：", "https://account.shinnytech.com/"
        ))

        layout.addWidget(make_divider())

        layout.addWidget(self._make_label(
            "3，登录你的快期客户端，从模拟银行转入资金到期货账户。"
        ))

        layout.addWidget(make_divider())

        layout.addWidget(self._make_label("4，在这里填入："))

        input_row = QWidget()
        # 透明须走全局 QSS 的 objectName 规则（theme.py）：
        # inline stylesheet 会隔断 app QSS 对行内按钮的类型级规则，导致按钮丢背景
        input_row.setObjectName("transparentBox")
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.sim_account_edit = QLineEdit()
        self.sim_account_edit.setPlaceholderText("快期模拟账户手机号")
        input_layout.addWidget(self.sim_account_edit, 1)

        self.sim_password_edit = QLineEdit()
        self.sim_password_edit.setPlaceholderText("快期模拟账户密码")
        self.sim_password_edit.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(self.sim_password_edit, 1)

        # 行内小按钮：覆盖全局按钮 QSS 的大 padding 与胶囊圆角，与输入框等高
        self.sim_password_toggle = make_button("", variant="secondary")
        self.sim_password_toggle.setStyleSheet(
            "padding: 0; min-height: 0; border-radius: 8px;"
        )
        # 图标按钮：宽度固定，垂直 Expanding 填满行高与输入框对齐
        self.sim_password_toggle.setFixedWidth(40)
        self.sim_password_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.sim_password_toggle.setCursor(Qt.PointingHandCursor)
        # 初始为密码隐藏态：睁眼图标 = 点击可查看
        self.sim_password_toggle.setIconSize(QSize(16, 16))
        self.sim_password_toggle.setIcon(_make_eye_icon(eye_off=False))
        self.sim_password_toggle.setToolTip("显示密码")
        self.sim_password_toggle.clicked.connect(self._toggle_password_visible)
        input_layout.addWidget(self.sim_password_toggle)

        self.save_btn = make_button("保存", variant="secondary")
        self.save_btn.setStyleSheet(
            "padding: 9px 14px; min-height: 0; border-radius: 8px; font-size: 13px;"
        )
        self.save_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.save_btn.clicked.connect(self._on_save_clicked)
        input_layout.addWidget(self.save_btn)

        self.test_btn = make_button("测试连接", variant="secondary")
        self.test_btn.setStyleSheet(
            "padding: 9px 14px; min-height: 0; border-radius: 8px; font-size: 13px;"
        )
        self.test_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.clicked.connect(self._on_test_clicked)
        input_layout.addWidget(self.test_btn)

        layout.addWidget(input_row)

        hint = QLabel("提示：模拟帐户不支持组合/套利和期权交易，仅国内商品和股指国债。")
        hint.setObjectName("dim")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch(1)
        self.content_layout.addWidget(card)

        self.on_save = None  # type: Optional[Callable[[dict], None]]
        self.on_test = None  # type: Optional[Callable[[str, str], None]]

        self.content_layout.addStretch(1)

    @staticmethod
    def _make_label(text: str) -> QLabel:
        label = QLabel(text)
        # 全局 QWidget 背景规则会让卡内 QLabel 露出灰条，强制透明
        label.setStyleSheet("background: transparent;")
        return label

    @staticmethod
    def _make_link_row(prefix: str, url: str) -> QLabel:
        # 链接色内联在富文本里：默认链接色在深色主题下几乎不可读，
        # palette.Link 会被全局 QSS 覆盖，内联 span 是唯一可靠的方式
        label = QLabel(
            f'{prefix}<a href="{url}"><span style="color:#007aff">{url}</span></a>'
        )
        label.setObjectName("dim")
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        return label

    def _toggle_password_visible(self):
        visible = self.sim_password_edit.echoMode() == QLineEdit.Normal
        self.sim_password_edit.setEchoMode(QLineEdit.Password if visible else QLineEdit.Normal)
        # 图标表示点击后的效果：隐藏时显示睁眼（点击查看），明文时显示闭眼（点击隐藏）
        hidden = visible  # 点击后的状态：原为明文则变隐藏
        self.sim_password_toggle.setIcon(_make_eye_icon(eye_off=not hidden))
        self.sim_password_toggle.setToolTip("显示密码" if hidden else "隐藏密码")

    def set_config(self, config: TradingConfiguration):
        """用当前配置填充表单（启动时以及配置保存后调用）。

        快期账户与实盘交易页共用，读写同一 tq_* 字段。
        """
        self.sim_account_edit.setText(config.tq_account)
        self.sim_password_edit.setText(config.tq_password)

    def _on_save_clicked(self):
        data = {
            "tq_account": self.sim_account_edit.text().strip(),
            "tq_password": self.sim_password_edit.text(),
        }

        if not data["tq_account"]:
            QMessageBox.warning(self, "输入错误", "手机号不能为空")
            return
        if not data["tq_password"]:
            QMessageBox.warning(self, "输入错误", "密码不能为空")
            return

        if self.on_save:
            self.on_save(data)
            QMessageBox.information(self, "保存成功", "模拟交易账户配置已保存")
        else:
            QMessageBox.warning(self, "错误", "保存回调未设置")

    def _on_test_clicked(self):
        account = self.sim_account_edit.text().strip()
        password = self.sim_password_edit.text()

        if not account:
            QMessageBox.warning(self, "输入错误", "手机号不能为空")
            return
        if not password:
            QMessageBox.warning(self, "输入错误", "密码不能为空")
            return

        if self.on_test:
            # 连接验证在后台进行，按钮置为不可用直至结果返回
            self.test_btn.setEnabled(False)
            self.test_btn.setText("测试中...")
            self.on_test(account, password)
        else:
            QMessageBox.warning(self, "错误", "测试回调未设置")

    def set_test_result(self, message: str, ok: bool):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")
        if ok:
            QMessageBox.information(self, "测试连接", message)
        else:
            QMessageBox.warning(self, "测试连接", message)


class FlowLayout(QLayout):
    """横向流式布局：子控件按行横向排列，超出可用宽度自动换行。"""

    def __init__(self, parent: Optional[QWidget] = None, spacing: int = 8):
        super().__init__(parent)
        self.setSpacing(spacing)
        self._items: list[QLayoutItem] = []

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x, y = effective.x(), effective.y()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + self.spacing()
            if next_x - self.spacing() > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y = y + line_height + self.spacing()
                next_x = x + hint.width() + self.spacing()
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())
        return y + line_height - rect.y() + margins.bottom()


class ServerUrlTestRow(QWidget):
    """服务器地址输入行：输入框 + 测试连接按钮 + 结果标签。

    on_test 由外部设置，接收规范化前的地址字符串；测试结果通过 set_result 回写。
    """

    def __init__(self, initial: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.help_btn.setStyleSheet(
            "QToolButton {"
            "color: #0066cc; font-weight: 600; font-size: 14px;"
            "border: 1px solid #e0e0e0; border-radius: 10px;"
            "background: transparent;"
            "min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;"
            "}"
            "QToolButton:hover { background: #f0f0f0; }"
            "QToolButton:pressed { background: #e0e0e0; }"
        )
        self.help_btn.clicked.connect(self._show_help)
        row.addWidget(self.help_btn)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:8000")
        if initial:
            self.url_edit.setText(initial)
        self.test_btn = make_button("测试连接", variant="secondary")
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.test_btn)
        outer.addLayout(row)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        outer.addWidget(self.result_label)

        self.on_test = None  # type: Optional[Callable[[str], None]]
        self.test_btn.clicked.connect(self._emit_test)
        self.url_edit.returnPressed.connect(self._emit_test)

    def _show_help(self):
        """点击问号图标后显示服务器地址说明。"""
        QToolTip.showText(
            self.help_btn.mapToGlobal(self.help_btn.rect().bottomLeft()),
            "<div style='font-size:13px; padding:4px;'>"
            "这是 <b>iTrader</b> 智能交易服务器的地址"
            "</div>",
        )

    def _emit_test(self):
        url = self.url_edit.text().strip()
        if not url:
            self.set_result("请先输入服务器地址", False)
            return
        self.test_btn.setEnabled(False)
        self._show("正在测试连接...", WARNING)
        if self.on_test:
            self.on_test(url)
        else:
            self.set_result("测试功能未启用", False)

    def _show(self, message: str, color: str):
        self.result_label.setVisible(True)
        self.result_label.setText(message)
        self.result_label.setStyleSheet(f"color: {color};")

    def set_result(self, message: str, success: Optional[bool]):
        color = WARNING if success is None else (SUCCESS if success else DANGER)
        self._show(message, color)
        self.test_btn.setEnabled(True)


class SettingsPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("设置", "服务器连接配置，保存后即时生效。")
        self.content_layout.addWidget(self.header)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        # macOS 平台默认 FieldsStayAtSizeHint 会导致字段列不撑宽、品种单选竖排
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.server_test = ServerUrlTestRow()
        self.server_url_edit = self.server_test.url_edit
        form.addRow("服务器地址:", self.server_test)

        server_hint = QLabel("这是 iTrader 智能交易服务器的地址，需与服务器部署地址一致")
        server_hint.setObjectName("dim")
        server_hint.setWordWrap(True)
        form.addRow("", server_hint)

        # 代理服务器：直连（默认，忽略系统代理）/ 系统代理 / 自定义代理地址 + 地址输入框同行
        self.proxy_mode_area = QWidget()
        self.proxy_mode_area.setStyleSheet("background: transparent;")
        proxy_mode_layout = QHBoxLayout(self.proxy_mode_area)
        proxy_mode_layout.setContentsMargins(0, 0, 0, 0)
        proxy_mode_layout.setSpacing(12)
        self._proxy_mode_group = QButtonGroup(self.proxy_mode_area)
        self._proxy_mode_group.setExclusive(True)
        self.proxy_direct_radio = QRadioButton("直连（默认）")
        self.proxy_system_radio = QRadioButton("系统代理")
        self.proxy_custom_radio = QRadioButton("自定义")
        for radio in (self.proxy_direct_radio, self.proxy_system_radio, self.proxy_custom_radio):
            self._proxy_mode_group.addButton(radio)
            radio.setCursor(Qt.PointingHandCursor)
            proxy_mode_layout.addWidget(radio)
        self.proxy_direct_radio.setChecked(True)
        self._proxy_mode_group.buttonClicked.connect(self._on_proxy_mode_changed)

        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("http://127.0.0.1:7890 或 socks5://127.0.0.1:1080")
        self.proxy_edit.setEnabled(False)
        proxy_mode_layout.addWidget(self.proxy_edit, 1)
        form.addRow("代理服务器:", self.proxy_mode_area)

        proxy_hint = QLabel("仅影响天勤行情/交易连接，iTrader 服务器始终直连；直连会忽略系统代理。socks5 代理需安装 python-socks")
        proxy_hint.setObjectName("dim")
        proxy_hint.setWordWrap(True)
        form.addRow("", proxy_hint)

        # 订阅品种：从服务器拉取可订阅列表，勾选后随保存写入配置
        self.symbol_refresh_btn = make_button("刷新品种", variant="secondary")
        self.symbol_status_label = QLabel("")
        self.symbol_status_label.setWordWrap(True)
        refresh_row = QHBoxLayout()
        refresh_row.setSpacing(8)
        refresh_row.addWidget(self.symbol_refresh_btn)
        refresh_row.addWidget(self.symbol_status_label, 1)

        self.symbols_box = QWidget()
        # 容器 QWidget 会匹配全局窗口底色规则，白卡内需显式透明
        self.symbols_box.setStyleSheet("background: transparent;")
        self.symbols_flow = FlowLayout(self.symbols_box, spacing=10)

        # 添加品种：先输入品种代码，再从服务器支持的交易所中单选，提交后持久化到品种库
        self.symbol_add_edit = QLineEdit()
        self.symbol_add_edit.setPlaceholderText("品种代码，例如 SHFE.au2510")
        self.symbol_add_btn = make_button("添加品种", variant="secondary")
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        add_row.addWidget(self.symbol_add_edit, 1)
        add_row.addWidget(self.symbol_add_btn)

        self.exchange_area = QWidget()
        self.exchange_area.setStyleSheet("background: transparent;")
        self.exchange_hint = QLabel("支持的交易所（单选）：")
        self.exchange_hint.setObjectName("dim")
        self.exchange_hint.setWordWrap(True)
        # FlowLayout 构造时即安装为父级布局，需由内层子控件承载
        self.exchange_box = QWidget()
        self.exchange_box.setStyleSheet("background: transparent;")
        self.exchange_flow = FlowLayout(self.exchange_box, spacing=10)
        exchange_layout = QVBoxLayout(self.exchange_area)
        exchange_layout.setContentsMargins(0, 0, 0, 0)
        exchange_layout.setSpacing(6)
        exchange_layout.addWidget(self.exchange_hint)
        exchange_layout.addWidget(self.exchange_box)
        # 没选（输入）交易品种之前，交易所不可选
        self.exchange_area.setEnabled(False)

        self.symbols_hint = QLabel("从服务器获取可订阅的品种列表后，选择要订阅的品种")
        self.symbols_hint.setObjectName("dim")
        self.symbols_hint.setWordWrap(True)

        symbols_panel = QWidget()
        symbols_panel.setStyleSheet("background: transparent;")
        symbols_layout = QVBoxLayout(symbols_panel)
        symbols_layout.setContentsMargins(0, 0, 0, 0)
        symbols_layout.setSpacing(8)
        symbols_layout.addLayout(refresh_row)
        symbols_layout.addLayout(add_row)
        symbols_layout.addWidget(self.exchange_area)
        symbols_layout.addWidget(self.symbols_box)
        symbols_layout.addWidget(self.symbols_hint)
        form.addRow("订阅品种:", symbols_panel)

        # 软件更新：手动检查入口 + 启动自动检查开关（随保存按钮持久化）
        form.addRow(make_divider())

        self.version_label = QLabel(f"当前版本 v{__version__}")
        self.update_check_btn = make_button("检查更新", variant="secondary")
        self.update_status_label = QLabel("")
        self.update_status_label.setWordWrap(True)
        update_row = QHBoxLayout()
        update_row.setSpacing(8)
        update_row.addWidget(self.version_label)
        update_row.addWidget(self.update_check_btn)
        update_row.addWidget(self.update_status_label, 1)
        form.addRow("软件更新:", update_row)

        self.auto_check_update_checkbox = QCheckBox("启动时自动检查更新，发现新版本时提示")
        form.addRow("", self.auto_check_update_checkbox)

        layout.addLayout(form)

        self.save_btn = make_button("保存", variant="primary")
        layout.addWidget(make_divider())
        layout.addWidget(self.save_btn, 0, Qt.AlignRight)
        self.save_btn.clicked.connect(self._on_save_clicked)

        layout.addStretch(1)
        self.content_layout.addWidget(card)

        # For compatibility, we keep the on_save callback to be set externally
        self.on_save = None  # type: Optional[Callable[[dict], None]]
        # 由外部（控制器）设置，接收规范化前的服务器地址
        self.on_fetch_symbols = None  # type: Optional[Callable[[str], None]]
        # 拉取交易所列表：接收服务器地址；提交品种：接收 (服务器地址, 品种, 交易所)
        self.on_fetch_exchanges = None  # type: Optional[Callable[[str], None]]
        self.on_submit_symbol = None  # type: Optional[Callable[[str, str, str], None]]
        # 手动检查更新（控制器注入）
        self.on_check_update = None  # type: Optional[Callable[[], None]]

        self._symbol_radios: list[QRadioButton] = []
        self._config_symbols: list[str] = []
        self._exchange_radios: list[QRadioButton] = []
        self._exchanges: list[str] = []

        self.symbol_refresh_btn.clicked.connect(self._emit_fetch_symbols)
        self.symbol_add_btn.clicked.connect(self._on_add_symbol_clicked)
        self.symbol_add_edit.textChanged.connect(self._on_symbol_text_changed)
        self.update_check_btn.clicked.connect(self.start_check_update)

        self.content_layout.addStretch(1)

    def set_config(self, config: TradingConfiguration):
        """用当前配置填充表单（启动时以及配置保存后调用）。"""
        self.server_url_edit.setText(config.server_url)
        self._set_proxy_value(config.proxy_url)
        self._config_symbols = list(config.symbols)
        self._sync_symbol_radios()
        self.auto_check_update_checkbox.setChecked(config.auto_check_update)

    def _set_proxy_value(self, proxy_url: str):
        """按存储值还原代理模式单选按钮与自定义地址输入框。"""
        proxy_url = (proxy_url or "").strip()
        if proxy_url == SYSTEM_PROXY:
            self.proxy_system_radio.setChecked(True)
            self.proxy_edit.clear()
        elif proxy_url:
            self.proxy_custom_radio.setChecked(True)
            self.proxy_edit.setText(proxy_url)
        else:
            self.proxy_direct_radio.setChecked(True)
            self.proxy_edit.clear()
        self.proxy_edit.setEnabled(self.proxy_custom_radio.isChecked())

    def _on_proxy_mode_changed(self, _button=None):
        self.proxy_edit.setEnabled(self.proxy_custom_radio.isChecked())

    def _current_proxy_value(self) -> str:
        if self.proxy_system_radio.isChecked():
            return SYSTEM_PROXY
        if self.proxy_custom_radio.isChecked():
            return self.proxy_edit.text().strip()
        return ""

    def start_check_update(self):
        """检查更新按钮：置灰防重入，结果经 set_update_status 回写后恢复。"""
        self.update_check_btn.setEnabled(False)
        self.set_update_status("正在检查更新...", None)
        if self.on_check_update is not None:
            self.on_check_update()
        else:
            self.set_update_status("检查更新功能未启用", False)

    def set_update_status(self, message: str, state=None):
        """回写检查更新结果：state 为 True 成功 / False 失败 / None 进行中。"""
        self.update_check_btn.setEnabled(True)
        self.update_status_label.setText(message)
        color = WARNING if state is None else (SUCCESS if state else DANGER)
        # 白卡内的 QLabel 会匹配全局窗口底色规则，需显式透明
        self.update_status_label.setStyleSheet(f"color: {color}; background: transparent;")

    def maybe_refresh_symbols(self):
        """切换到设置页时自动拉取品种与交易所列表；地址为空时跳过。"""
        url = self.server_url_edit.text().strip()
        if not url:
            return
        if self.on_fetch_symbols is not None:
            self._emit_fetch_symbols()
        if self.on_fetch_exchanges is not None:
            self.on_fetch_exchanges(url)

    def set_symbols_result(self, success: bool, message: str, symbols: list):
        """刷新品种请求的完成回调（由控制器的信号驱动，UI 线程执行）。"""
        self.symbol_refresh_btn.setEnabled(True)
        self._set_symbol_status(message, SUCCESS if success else DANGER)
        if success:
            self._rebuild_symbol_radios(symbols)

    def set_exchanges_result(self, success: bool, message: str, exchanges: list):
        """交易所列表请求的完成回调（由控制器的信号驱动，UI 线程执行）。"""
        if success:
            self._exchanges = [
                str(item["name"]) for item in exchanges
                if isinstance(item, dict) and item.get("name")
            ]
            self.exchange_hint.setText("支持的交易所（单选）：")
            self.exchange_hint.setStyleSheet("")
        else:
            self._exchanges = []
            self.exchange_hint.setText(f"获取交易所失败: {message}")
            self.exchange_hint.setStyleSheet(f"color: {WARNING}; background: transparent;")
        self._rebuild_exchange_radios()

    def set_symbol_submit_result(self, success: bool, message: str):
        """添加品种请求的完成回调（由控制器的信号驱动，UI 线程执行）。"""
        self.symbol_add_btn.setEnabled(True)
        self._set_symbol_status(message, SUCCESS if success else DANGER)
        if success:
            # 清空品种输入（交易所随之回到禁用态），并刷新品种列表让新品种立即可选
            self.symbol_add_edit.clear()
            self._emit_fetch_symbols()

    def _on_symbol_text_changed(self, text: str):
        """先选（输入）交易品种，之后交易所才可选。"""
        self.exchange_area.setEnabled(bool(text.strip()))

    def _rebuild_exchange_radios(self):
        """重建交易所单选项；同属 exchange_area 的 QRadioButton 自动互斥。"""
        while self.exchange_flow.count():
            item = self.exchange_flow.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._exchange_radios = []

        for index, name in enumerate(self._exchanges):
            radio = QRadioButton(name, self.exchange_box)
            radio.setChecked(index == 0)
            radio.setCursor(Qt.PointingHandCursor)
            self.exchange_flow.addWidget(radio)
            self._exchange_radios.append(radio)

    def _selected_exchange(self) -> str:
        for radio in self._exchange_radios:
            if radio.isChecked():
                return radio.text()
        return ""

    def _on_add_symbol_clicked(self):
        url = self.server_url_edit.text().strip()
        if not url:
            self._set_symbol_status("请先填写服务器地址", DANGER)
            return
        symbol = self.symbol_add_edit.text().strip()
        if not symbol:
            self._set_symbol_status("请输入品种代码", DANGER)
            return
        exchange = self._selected_exchange()
        if not exchange:
            self._set_symbol_status("请选择交易所", DANGER)
            return
        self.symbol_add_btn.setEnabled(False)
        self._set_symbol_status("正在添加品种...", WARNING)
        if self.on_submit_symbol:
            self.on_submit_symbol(url, symbol, exchange)
        else:
            self._set_symbol_status("添加品种功能未启用", DANGER)
            self.symbol_add_btn.setEnabled(True)

    def _set_symbol_status(self, message: str, color: str):
        self.symbol_status_label.setText(message)
        self.symbol_status_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def _emit_fetch_symbols(self):
        url = self.server_url_edit.text().strip()
        if not url:
            self._set_symbol_status("请先填写服务器地址", DANGER)
            return
        self.symbol_refresh_btn.setEnabled(False)
        self._set_symbol_status("正在获取品种...", WARNING)
        if self.on_fetch_symbols:
            self.on_fetch_symbols(url)
        else:
            self._set_symbol_status("获取品种功能未启用", DANGER)
            self.symbol_refresh_btn.setEnabled(True)

    def _rebuild_symbol_radios(self, server_symbols: list):
        """按服务器返回重建单选项；配置中存在但服务器未返回的品种保留显示，避免静默丢失。"""
        merged = [str(s) for s in server_symbols]
        for symbol in self._config_symbols:
            if symbol not in merged:
                merged.append(symbol)

        while self.symbols_flow.count():
            item = self.symbols_flow.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._symbol_radios = []

        # 系统一次只订阅一个品种：历史配置含多个时，仅选中第一个匹配项
        selected = next((s for s in self._config_symbols if s in merged), None)

        for symbol in merged:
            radio = QRadioButton(symbol, self.symbols_box)
            radio.setChecked(symbol == selected)
            radio.setCursor(Qt.PointingHandCursor)
            self.symbols_flow.addWidget(radio)
            self._symbol_radios.append(radio)

        if merged:
            self.symbols_hint.setText(f"共 {len(merged)} 个品种，选择要订阅的品种，保存后生效")
        else:
            self.symbols_hint.setText("服务器暂无可订阅品种")

    def _sync_symbol_radios(self):
        """把选中状态同步为当前配置中的品种（配置变化后调用）。"""
        available = {radio.text() for radio in self._symbol_radios}
        selected = next((s for s in self._config_symbols if s in available), None)
        for radio in self._symbol_radios:
            radio.setChecked(radio.text() == selected)

    def _on_save_clicked(self):
        data = {
            "server_url": self.server_url_edit.text().strip(),
            "proxy_url": self._current_proxy_value(),
            "auto_check_update": self.auto_check_update_checkbox.isChecked(),
        }

        # Validate
        if not data["server_url"]:
            QMessageBox.warning(self, "输入错误", "服务器地址不能为空")
            return

        # 仅在已获取到品种列表时提交选择结果；未获取过则保留现有订阅不变
        if self._symbol_radios:
            selected = [radio.text() for radio in self._symbol_radios if radio.isChecked()]
            if not selected:
                QMessageBox.warning(self, "输入错误", "请选择一个订阅品种")
                return
            data["symbols"] = selected[0]

        # Call the external save callback
        if self.on_save:
            self.on_save(data)
            QMessageBox.information(self, "保存成功", "配置已保存并生效")
        else:
            QMessageBox.warning(self, "错误", "保存回调未设置")


class AccountPage(BasePage):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.header = PageHeader("实盘交易", "期货公司、资金账号、交易密码与快期账户，保存后即时生效。")
        self.content_layout.addWidget(self.header)

        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        # macOS 平台默认 FieldsStayAtSizeHint 会导致字段列不撑宽、期货公司单选竖排
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 期货公司：按天勤版本分组横向单选，选择结果持久化到 broker.json
        self.broker_area = QWidget()
        # 容器 QWidget 会匹配全局窗口底色规则，白卡内需显式透明
        self.broker_area.setStyleSheet("background: transparent;")
        broker_layout = QVBoxLayout(self.broker_area)
        broker_layout.setContentsMargins(0, 0, 0, 0)
        broker_layout.setSpacing(6)
        self._broker_group = QButtonGroup(self.broker_area)
        self._broker_group.setExclusive(True)
        self._broker_rows: list[QWidget] = []
        form.addRow("期货公司:", self.broker_area)

        self.trade_account_edit = QLineEdit()
        self.trade_account_edit.setPlaceholderText("资金账号 (实盘必填)")
        form.addRow("资金账号:", self.trade_account_edit)

        self.trade_password_edit = QLineEdit()
        self.trade_password_edit.setPlaceholderText("交易密码 (实盘必填)")
        self.trade_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("交易密码:", self.trade_password_edit)

        self.tq_account_edit = QLineEdit()
        self.tq_account_edit.setPlaceholderText("快期账号")
        form.addRow("快期账号:", self.tq_account_edit)

        self.tq_password_edit = QLineEdit()
        self.tq_password_edit.setPlaceholderText("快期密码")
        self.tq_password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("快期密码:", self.tq_password_edit)

        self.balance_edit = QLineEdit()
        self.balance_edit.setPlaceholderText("10000000")
        form.addRow("初始资金:", self.balance_edit)

        self.symbols_edit = QLineEdit()
        self.symbols_edit.setPlaceholderText("品种1,品种2,...")
        form.addRow("交易品种:", self.symbols_edit)

        symbols_hint = QLabel("品种以逗号分隔，例如: SHFE.au2510,INE.sc2510")
        symbols_hint.setObjectName("dim")
        form.addRow("", symbols_hint)

        layout.addLayout(form)

        self.save_btn = make_button("保存", variant="primary")
        layout.addWidget(make_divider())
        layout.addWidget(self.save_btn, 0, Qt.AlignRight)
        self.save_btn.clicked.connect(self._on_save_clicked)

        # 受限于 TqSdk，我们支持的期货公司参见：tqsdk-brokers
        broker_hint = QLabel(
            "受限于 TqSdk，我们支持的期货公司参见："
            '<a href="https://www.shinnytech.com/articles/reference/tqsdk-brokers">'
            "tqsdk-brokers</a>"
        )
        broker_hint.setObjectName("dim")
        broker_hint.setOpenExternalLinks(True)
        broker_hint.setTextInteractionFlags(Qt.TextBrowserInteraction)
        layout.addWidget(broker_hint)

        layout.addStretch(1)
        self.content_layout.addWidget(card)

        self.on_save = None  # type: Optional[Callable[[dict], None]]

        self.content_layout.addStretch(1)

    def set_config(self, config: TradingConfiguration):
        """用当前配置填充表单（启动时以及配置保存后调用）。"""
        self.trade_account_edit.setText(config.trade_account)
        self.trade_password_edit.setText(config.trade_password)
        self.tq_account_edit.setText(config.tq_account)
        self.tq_password_edit.setText(config.tq_password)
        self.balance_edit.setText(str(config.initial_balance))
        self.symbols_edit.setText(",".join(config.symbols))

    def set_brokers(self, groups: dict, selected: str = ""):
        """按天勤版本分组构建期货公司单选项（每组一行、横向排列）。"""
        for row_box in self._broker_rows:
            row_box.deleteLater()
        self._broker_rows = []

        # QButtonGroup 无 removeButton，重建时整个组重建
        self._broker_group.deleteLater()
        self._broker_group = QButtonGroup(self.broker_area)
        self._broker_group.setExclusive(True)

        names = [name for group in groups.values() for name in group]
        checked_name = selected if selected in names else (names[0] if names else "")

        layout = self.broker_area.layout()
        for group_name, brokers in groups.items():
            row_box = QWidget(self.broker_area)
            row_box.setStyleSheet("background: transparent;")
            row = QHBoxLayout(row_box)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)
            group_label = QLabel(f"{group_name}:", row_box)
            group_label.setObjectName("dim")
            row.addWidget(group_label)
            for name in brokers:
                radio = QRadioButton(name, row_box)
                # 免费/专业版分行显示、分属不同父级，需同一 QButtonGroup 保证跨组单选
                self._broker_group.addButton(radio)
                radio.setChecked(name == checked_name)
                radio.setCursor(Qt.PointingHandCursor)
                row.addWidget(radio)
            row.addStretch(1)
            layout.addWidget(row_box)
            self._broker_rows.append(row_box)

    def _selected_broker(self) -> str:
        checked = self._broker_group.checkedButton()
        return checked.text() if checked else ""

    def _on_save_clicked(self):
        data = {
            "broker": self._selected_broker(),
            "trade_account": self.trade_account_edit.text().strip(),
            "trade_password": self.trade_password_edit.text(),
            "tq_account": self.tq_account_edit.text().strip(),
            "tq_password": self.tq_password_edit.text(),
            "initial_balance": self.balance_edit.text().strip(),
            "symbols": self.symbols_edit.text().strip(),
        }

        # Validate
        if not data["broker"]:
            QMessageBox.warning(self, "输入错误", "请选择期货公司")
            return
        if (data["trade_account"] and not data["trade_password"]) or (data["trade_password"] and not data["trade_account"]):
            QMessageBox.warning(self, "输入错误", "资金账号与交易密码需同时填写")
            return
        if not data["tq_account"]:
            QMessageBox.warning(self, "输入错误", "快期账号不能为空")
            return
        if not data["tq_password"]:
            QMessageBox.warning(self, "输入错误", "快期密码不能为空")
            return
        if not data["initial_balance"]:
            QMessageBox.warning(self, "输入错误", "初始资金不能为空")
            return
        try:
            balance = float(data["initial_balance"])
            if balance <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "初始资金必须是正数")
            return
        if not data["symbols"]:
            QMessageBox.warning(self, "输入错误", "交易品种不能为空")
            return

        # Call the external save callback
        if self.on_save:
            self.on_save(data)
            QMessageBox.information(self, "保存成功", "配置已保存并生效")
        else:
            QMessageBox.warning(self, "错误", "保存回调未设置")
