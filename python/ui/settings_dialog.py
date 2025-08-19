"""
设置对话框模块，提供系统设置界面
"""

from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLineEdit, QCheckBox, QSpinBox,
    QPushButton, QLabel, QComboBox, QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot

from python.utils.config_manager import ConfigManager
from python.utils.logger import LoggerMixin

class SettingsDialog(QDialog, LoggerMixin):
    """设置对话框"""
    
    def __init__(self, config: ConfigManager, parent=None):
        """
        初始化设置对话框
        
        Args:
            config: 配置管理器
            parent: 父窗口部件
        """
        super().__init__(parent)
        self.setup_logger("SettingsDialog")
        self.config = config
        
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        
        # 创建UI
        self.create_ui()
        
        # 加载设置
        self.load_settings()
    
    def create_ui(self) -> None:
        """创建用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡部件
        tab_widget = QTabWidget()
        
        # 创建通用设置标签页
        self.create_general_tab(tab_widget)
        
        # 创建账号设置标签页
        self.create_account_tab(tab_widget)
        
        # 创建通知设置标签页
        self.create_notification_tab(tab_widget)
        
        # 创建代理设置标签页
        self.create_proxy_tab(tab_widget)
        
        # 创建浏览器设置标签页
        self.create_browser_tab(tab_widget)
        
        # 添加选项卡部件到主布局
        main_layout.addWidget(tab_widget)
        
        # 创建按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def create_general_tab(self, tab_widget: QTabWidget) -> None:
        """
        创建通用设置标签页
        
        Args:
            tab_widget: 选项卡部件
        """
        general_tab = QWidget()
        layout = QVBoxLayout(general_tab)
        
        # 票务网站选择组
        site_group = QGroupBox("票务网站")
        site_layout = QFormLayout(site_group)
        
        self.site_combo = QComboBox()
        self.site_combo.addItems(["Interpark", "Yes24", "Melon"])
        site_layout.addRow("选择票务网站:", self.site_combo)
        
        layout.addWidget(site_group)
        
        # 抢票设置组
        grabbing_group = QGroupBox("抢票设置")
        grabbing_layout = QFormLayout(grabbing_group)
        
        self.refresh_interval = QDoubleSpinBox()
        self.refresh_interval.setRange(0.1, 10.0)
        self.refresh_interval.setSingleStep(0.1)
        self.refresh_interval.setSuffix(" 秒")
        grabbing_layout.addRow("刷新间隔:", self.refresh_interval)
        
        self.auto_refresh = QCheckBox("启用")
        grabbing_layout.addRow("自动刷新:", self.auto_refresh)
        
        layout.addWidget(grabbing_group)
        
        # 添加到选项卡
        tab_widget.addTab(general_tab, "通用设置")
    
    def create_account_tab(self, tab_widget: QTabWidget) -> None:
        """
        创建账号设置标签页
        
        Args:
            tab_widget: 选项卡部件
        """
        account_tab = QWidget()
        layout = QVBoxLayout(account_tab)
        
        # 账号设置组
        account_group = QGroupBox("账号信息")
        account_layout = QFormLayout(account_group)
        
        self.username = QLineEdit()
        account_layout.addRow("用户名:", self.username)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        account_layout.addRow("密码:", self.password)
        
        layout.addWidget(account_group)
        
        # 添加到选项卡
        tab_widget.addTab(account_tab, "账号设置")
    
    def create_notification_tab(self, tab_widget: QTabWidget) -> None:
        """
        创建通知设置标签页
        
        Args:
            tab_widget: 选项卡部件
        """
        notification_tab = QWidget()
        layout = QVBoxLayout(notification_tab)
        
        # 邮件通知组
        email_group = QGroupBox("邮件通知")
        email_layout = QFormLayout(email_group)
        
        self.email_enabled = QCheckBox("启用")
        email_layout.addRow("邮件通知:", self.email_enabled)
        
        self.smtp_server = QLineEdit()
        email_layout.addRow("SMTP服务器:", self.smtp_server)
        
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        email_layout.addRow("SMTP端口:", self.smtp_port)
        
        self.email_sender = QLineEdit()
        email_layout.addRow("发件人:", self.email_sender)
        
        self.email_password = QLineEdit()
        self.email_password.setEchoMode(QLineEdit.Password)
        email_layout.addRow("邮箱密码:", self.email_password)
        
        self.email_recipient = QLineEdit()
        email_layout.addRow("收件人:", self.email_recipient)
        
        # 测试邮件按钮
        test_email_btn = QPushButton("测试邮件")
        test_email_btn.clicked.connect(self.test_email)
        email_layout.addRow("", test_email_btn)
        
        layout.addWidget(email_group)
        
        # Telegram通知组
        telegram_group = QGroupBox("Telegram通知")
        telegram_layout = QFormLayout(telegram_group)
        
        self.telegram_enabled = QCheckBox("启用")
        telegram_layout.addRow("Telegram通知:", self.telegram_enabled)
        
        self.telegram_token = QLineEdit()
        telegram_layout.addRow("Bot Token:", self.telegram_token)
        
        self.telegram_chat_id = QLineEdit()
        telegram_layout.addRow("Chat ID:", self.telegram_chat_id)
        
        # 测试Telegram按钮
        test_telegram_btn = QPushButton("测试Telegram")
        test_telegram_btn.clicked.connect(self.test_telegram)
        telegram_layout.addRow("", test_telegram_btn)
        
        layout.addWidget(telegram_group)
        
        # 添加到选项卡
        tab_widget.addTab(notification_tab, "通知设置")
    
    def create_proxy_tab(self, tab_widget: QTabWidget) -> None:
        """
        创建代理设置标签页
        
        Args:
            tab_widget: 选项卡部件
        """
        proxy_tab = QWidget()
        layout = QVBoxLayout(proxy_tab)
        
        # 代理设置组
        proxy_group = QGroupBox("HTTP代理")
        proxy_layout = QFormLayout(proxy_group)
        
        self.proxy = QLineEdit()
        self.proxy.setPlaceholderText("例如: http://127.0.0.1:7890")
        proxy_layout.addRow("代理地址:", self.proxy)
        
        layout.addWidget(proxy_group)
        
        # 说明文字
        help_text = QLabel(
            "使用代理可以避免IP被封，格式为：http://host:port 或 socks5://host:port"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
        
        # 添加到选项卡
        tab_widget.addTab(proxy_tab, "代理设置")
    
    def create_browser_tab(self, tab_widget: QTabWidget) -> None:
        """
        创建浏览器设置标签页
        
        Args:
            tab_widget: 选项卡部件
        """
        browser_tab = QWidget()
        layout = QVBoxLayout(browser_tab)
        
        # 浏览器设置组
        browser_group = QGroupBox("浏览器设置")
        browser_layout = QFormLayout(browser_group)
        
        self.headless = QCheckBox("启用")
        browser_layout.addRow("无头模式:", self.headless)
        
        self.user_agent = QLineEdit()
        self.user_agent.setPlaceholderText("Mozilla/5.0 ...")
        browser_layout.addRow("User Agent:", self.user_agent)
        
        layout.addWidget(browser_group)
        
        # 说明文字
        help_text = QLabel(
            "无头模式下，浏览器窗口不会显示。这在服务器环境下很有用，但可能导致某些网站检测到机器人行为。"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
        
        # 添加到选项卡
        tab_widget.addTab(browser_tab, "浏览器设置")
    
    def load_settings(self) -> None:
        """加载设置"""
        # 通用设置
        site = self.config.get("ticketing_site", "interpark").lower()
        site_index = 0
        if site == "yes24":
            site_index = 1
        elif site == "melon":
            site_index = 2
        self.site_combo.setCurrentIndex(site_index)
        
        self.refresh_interval.setValue(self.config.get("refresh_interval", 0.5))
        self.auto_refresh.setChecked(self.config.get("auto_refresh", True))
        
        # 账号设置
        self.username.setText(self.config.get("username", ""))
        self.password.setText(self.config.get("password", ""))
        
        # 邮件通知设置
        self.email_enabled.setChecked(self.config.get("notification.email.enabled", False))
        self.smtp_server.setText(self.config.get("notification.email.smtp_server", ""))
        self.smtp_port.setValue(self.config.get("notification.email.smtp_port", 587))
        self.email_sender.setText(self.config.get("notification.email.sender", ""))
        self.email_password.setText(self.config.get("notification.email.password", ""))
        self.email_recipient.setText(self.config.get("notification.email.recipient", ""))
        
        # Telegram通知设置
        self.telegram_enabled.setChecked(self.config.get("notification.telegram.enabled", False))
        self.telegram_token.setText(self.config.get("notification.telegram.bot_token", ""))
        self.telegram_chat_id.setText(self.config.get("notification.telegram.chat_id", ""))
        
        # 代理设置
        self.proxy.setText(self.config.get("proxy", ""))
        
        # 浏览器设置
        self.headless.setChecked(self.config.get("browser.headless", False))
        self.user_agent.setText(self.config.get("browser.user_agent", ""))
    
    def accept(self) -> None:
        """接受设置更改"""
        # 保存通用设置
        sites = ["interpark", "yes24", "melon"]
        site_index = self.site_combo.currentIndex()
        self.config.set("ticketing_site", sites[site_index])
        
        self.config.set("refresh_interval", self.refresh_interval.value())
        self.config.set("auto_refresh", self.auto_refresh.isChecked())
        
        # 保存账号设置
        self.config.set("username", self.username.text())
        self.config.set("password", self.password.text())
        
        # 保存邮件通知设置
        self.config.set("notification.email.enabled", self.email_enabled.isChecked())
        self.config.set("notification.email.smtp_server", self.smtp_server.text())
        self.config.set("notification.email.smtp_port", self.smtp_port.value())
        self.config.set("notification.email.sender", self.email_sender.text())
        self.config.set("notification.email.password", self.email_password.text())
        self.config.set("notification.email.recipient", self.email_recipient.text())
        
        # 保存Telegram通知设置
        self.config.set("notification.telegram.enabled", self.telegram_enabled.isChecked())
        self.config.set("notification.telegram.bot_token", self.telegram_token.text())
        self.config.set("notification.telegram.chat_id", self.telegram_chat_id.text())
        
        # 保存代理设置
        self.config.set("proxy", self.proxy.text())
        
        # 保存浏览器设置
        self.config.set("browser.headless", self.headless.isChecked())
        self.config.set("browser.user_agent", self.user_agent.text())
        
        self.logger.info("设置已保存")
        super().accept()
    
    @pyqtSlot()
    def test_email(self) -> None:
        """测试邮件通知"""
        if not self.email_enabled.isChecked():
            QMessageBox.warning(self, "警告", "请先启用邮件通知")
            return
            
        if not self.smtp_server.text() or not self.email_sender.text() or not self.email_password.text() or not self.email_recipient.text():
            QMessageBox.warning(self, "警告", "请填写完整的邮件设置")
            return
            
        # 临时保存设置
        self.config.set("notification.email.enabled", True)
        self.config.set("notification.email.smtp_server", self.smtp_server.text())
        self.config.set("notification.email.smtp_port", self.smtp_port.value())
        self.config.set("notification.email.sender", self.email_sender.text())
        self.config.set("notification.email.password", self.email_password.text())
        self.config.set("notification.email.recipient", self.email_recipient.text())
        
        # 创建通知管理器
        from python.utils.notification import NotificationManager
        notification = NotificationManager(self.config)
        
        # 发送测试邮件
        QMessageBox.information(self, "测试中", "正在发送测试邮件，请稍候...")
        
        success = notification.send_email("抢票系统测试邮件", "这是一封测试邮件，如果您收到这封邮件，说明邮件通知设置正确。")
        
        if success:
            QMessageBox.information(self, "成功", "测试邮件已发送，请检查收件箱")
        else:
            QMessageBox.critical(self, "失败", "发送测试邮件失败，请检查设置")
    
    @pyqtSlot()
    def test_telegram(self) -> None:
        """测试Telegram通知"""
        if not self.telegram_enabled.isChecked():
            QMessageBox.warning(self, "警告", "请先启用Telegram通知")
            return
            
        if not self.telegram_token.text() or not self.telegram_chat_id.text():
            QMessageBox.warning(self, "警告", "请填写Bot Token和Chat ID")
            return
            
        # 临时保存设置
        self.config.set("notification.telegram.enabled", True)
        self.config.set("notification.telegram.bot_token", self.telegram_token.text())
        self.config.set("notification.telegram.chat_id", self.telegram_chat_id.text())
        
        # 创建通知管理器
        from python.utils.notification import NotificationManager
        notification = NotificationManager(self.config)
        
        # 发送测试消息
        QMessageBox.information(self, "测试中", "正在发送Telegram测试消息，请稍候...")
        
        success = notification.send_telegram("抢票系统测试", "这是一条测试消息，如果您收到这条消息，说明Telegram通知设置正确。")
        
        if success:
            QMessageBox.information(self, "成功", "Telegram测试消息已发送")
        else:
            QMessageBox.critical(self, "失败", "发送Telegram测试消息失败，请检查设置")