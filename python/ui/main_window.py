"""
主窗口模块，提供抢票系统的主界面
"""

import sys
import os
import time
import threading
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QStatusBar, QMessageBox, QComboBox, QCheckBox, QTabWidget,
    QLineEdit, QFormLayout, QGroupBox, QToolBar, QAction, QFileDialog,
    QMenu, QSystemTrayIcon, QProgressBar, QSpinBox, QDoubleSpinBox,
    QPlainTextEdit
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QTextCursor, QCloseEvent
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QSize, QThread

from python.utils.config_manager import ConfigManager
from python.utils.logger import LoggerMixin, get_logger
from python.utils.notification import NotificationManager
from python.core.ticket_bot import TicketBot
from python.ui.settings_dialog import SettingsDialog

class ConcertTableModel:
    """演唱会表格数据模型"""
    
    def __init__(self):
        self.concerts: List[Dict[str, Any]] = []
        
    def load_from_config(self, config: ConfigManager) -> None:
        """从配置中加载演唱会数据"""
        self.concerts = config.get_all_concerts()
        
    def add_concert(self, concert: Dict[str, Any]) -> None:
        """添加演唱会"""
        self.concerts.append(concert)
        
    def remove_concert(self, index: int) -> None:
        """移除演唱会"""
        if 0 <= index < len(self.concerts):
            del self.concerts[index]
            
    def get_concert(self, index: int) -> Optional[Dict[str, Any]]:
        """获取演唱会信息"""
        if 0 <= index < len(self.concerts):
            return self.concerts[index]
        return None
    
    def get_all_concerts(self) -> List[Dict[str, Any]]:
        """获取所有演唱会"""
        return self.concerts
        
    def get_count(self) -> int:
        """获取演唱会数量"""
        return len(self.concerts)
        
    def save_to_config(self, config: ConfigManager) -> None:
        """保存演唱会数据到配置"""
        for concert in self.concerts:
            config.add_concert(concert)
        config.save()

class LogTextHandler:
    """日志处理器，将日志消息发送到UI"""
    
    def __init__(self, signal):
        self.signal = signal
        
    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

class MainWindow(QMainWindow, LoggerMixin):
    """抢票系统主窗口"""
    
    # 自定义信号
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setup_logger("MainWindow")
        
        # 配置管理器
        self.config = ConfigManager()
        
        # 演唱会数据模型
        self.concert_model = ConcertTableModel()
        self.concert_model.load_from_config(self.config)
        
        # 抢票会话
        self.grabbing_session = None
        # Go 抢票子进程与线程
        self.go_processes = {}
        self.go_threads = []
        
        # 状态标志
        self.is_running = False
        self.stopping = False
        
        # 设置窗口
        self.setWindowTitle("韩国演唱会抢票系统")
        self.setMinimumSize(800, 600)
        
        # 创建UI
        self.create_ui()
        
        # 连接信号和槽
        self.connect_signals()
        
        # 加载数据
        self.load_data()
        
        # 初始化系统托盘
        self.setup_tray()
        
        self.logger.info("主窗口已初始化")
    
    def create_ui(self) -> None:
        """创建用户界面"""
        # 创建中央窗口部件和布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡窗口部件
        self.tab_widget = QTabWidget()
        
        # 创建抢票标签页
        self.create_grabbing_tab()
        
        # 创建演唱会管理标签页
        self.create_concerts_tab()
        
        # 创建日志标签页
        self.create_log_tab()
        
        # 添加选项卡到布局
        main_layout.addWidget(self.tab_widget)
        
        # 设置中央窗口部件
        self.setCentralWidget(central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_statusbar()
        
        # 设置样式
        self.apply_styles()
    
    def create_grabbing_tab(self) -> None:
        """创建抢票标签页"""
        grabbing_tab = QWidget()
        layout = QVBoxLayout(grabbing_tab)
        
        # 创建演唱会选择组
        concerts_group = QGroupBox("要抢的演唱会")
        concerts_layout = QVBoxLayout(concerts_group)
        
        # 演唱会列表
        self.concerts_table = QTableWidget()
        self.concerts_table.setColumnCount(5)
        self.concerts_table.setHorizontalHeaderLabels(["选择", "演唱会名称", "日期", "场馆", "状态"])
        self.concerts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        concerts_layout.addWidget(self.concerts_table)
        layout.addWidget(concerts_group)
        
        # 创建操作按钮组
        button_layout = QHBoxLayout()
        
        # 添加刷新间隔设置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("刷新间隔:"))
        self.refresh_interval = QDoubleSpinBox()
        self.refresh_interval.setRange(0.1, 10.0)
        self.refresh_interval.setValue(0.5)
        self.refresh_interval.setSingleStep(0.1)
        self.refresh_interval.setSuffix(" 秒")
        interval_layout.addWidget(self.refresh_interval)
        
        button_layout.addLayout(interval_layout)
        
        # 添加自动刷新选项
        self.auto_refresh_checkbox = QCheckBox("自动刷新")
        self.auto_refresh_checkbox.setChecked(True)
        button_layout.addWidget(self.auto_refresh_checkbox)
        
        button_layout.addStretch()
        
        # 开始抢票按钮
        self.start_button = QPushButton("开始抢票")
        self.start_button.setMinimumWidth(120)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.start_button)
        
        # 停止抢票按钮
        self.stop_button = QPushButton("停止抢票")
        self.stop_button.setMinimumWidth(120)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # 添加进度显示
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("抢票进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        # 添加到选项卡
        self.tab_widget.addTab(grabbing_tab, "抢票")
    
    def create_concerts_tab(self) -> None:
        """创建演唱会管理标签页"""
        concerts_tab = QWidget()
        layout = QVBoxLayout(concerts_tab)
        
        # 创建演唱会管理组
        manage_group = QGroupBox("演唱会管理")
        manage_layout = QVBoxLayout(manage_group)
        
        # 创建演唱会表格
        self.manage_table = QTableWidget()
        self.manage_table.setColumnCount(6)
        self.manage_table.setHorizontalHeaderLabels(["ID", "演唱会名称", "日期", "场馆", "价格限制", "操作"])
        self.manage_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        manage_layout.addWidget(self.manage_table)
        
        # 创建操作按钮
        button_layout = QHBoxLayout()
        
        self.add_concert_button = QPushButton("添加演唱会")
        self.add_concert_button.setStyleSheet("background-color: #2196F3; color: white;")
        button_layout.addWidget(self.add_concert_button)
        
        self.import_button = QPushButton("导入演唱会")
        button_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("导出演唱会")
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        
        self.save_concerts_button = QPushButton("保存更改")
        self.save_concerts_button.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.save_concerts_button)
        
        manage_layout.addLayout(button_layout)
        
        layout.addWidget(manage_group)
        
        # 创建演唱会详情组
        details_group = QGroupBox("演唱会详情")
        details_layout = QFormLayout(details_group)
        
        self.concert_id_edit = QLineEdit()
        details_layout.addRow("ID:", self.concert_id_edit)
        
        self.concert_name_edit = QLineEdit()
        details_layout.addRow("名称:", self.concert_name_edit)
        
        self.concert_date_edit = QLineEdit()
        details_layout.addRow("日期:", self.concert_date_edit)
        
        self.concert_venue_edit = QLineEdit()
        details_layout.addRow("场馆:", self.concert_venue_edit)
        
        self.concert_url_edit = QLineEdit()
        details_layout.addRow("URL:", self.concert_url_edit)
        
        self.concert_price_edit = QSpinBox()
        self.concert_price_edit.setRange(0, 1000000)
        self.concert_price_edit.setSingleStep(10000)
        self.concert_price_edit.setSuffix(" 韩元")
        details_layout.addRow("价格限制:", self.concert_price_edit)
        
        self.concert_preferences_edit = QLineEdit()
        details_layout.addRow("座位偏好:", self.concert_preferences_edit)
        
        layout.addWidget(details_group)
        
        # 添加到选项卡
        self.tab_widget.addTab(concerts_tab, "演唱会管理")
    
    def create_log_tab(self) -> None:
        """创建日志标签页"""
        log_tab = QWidget()
        layout = QVBoxLayout(log_tab)
        
        # 日志文本显示
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.clear_log_button = QPushButton("清除日志")
        button_layout.addWidget(self.clear_log_button)
        
        self.save_log_button = QPushButton("保存日志")
        button_layout.addWidget(self.save_log_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 添加到选项卡
        self.tab_widget.addTab(log_tab, "日志")
    
    def create_toolbar(self) -> None:
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 添加设置按钮
        settings_action = QAction(QIcon(":/icons/settings.png"), "设置", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        toolbar.addAction(settings_action)
        
        # 添加分隔符
        toolbar.addSeparator()
        
        # 添加刷新按钮
        refresh_action = QAction(QIcon(":/icons/refresh.png"), "刷新", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # 添加分隔符
        toolbar.addSeparator()
        
        # 添加帮助按钮
        help_action = QAction(QIcon(":/icons/help.png"), "帮助", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
    
    def create_statusbar(self) -> None:
        """创建状态栏"""
        self.statusbar = self.statusBar()
        self.statusbar.showMessage("就绪")
    
    def apply_styles(self) -> None:
        """应用样式"""
        # 这里可以添加样式表来自定义界面外观
        pass
    
    def connect_signals(self) -> None:
        """连接信号和槽"""
        # 抢票按钮
        self.start_button.clicked.connect(self.start_grabbing)
        self.stop_button.clicked.connect(self.stop_grabbing)
        
        # 演唱会管理按钮
        self.add_concert_button.clicked.connect(self.add_new_concert)
        self.import_button.clicked.connect(self.import_concerts)
        self.export_button.clicked.connect(self.export_concerts)
        self.save_concerts_button.clicked.connect(self.save_concerts)
        
        # 日志按钮
        self.clear_log_button.clicked.connect(self.clear_log)
        self.save_log_button.clicked.connect(self.save_log)
        
        # 管理表格选择事件
        self.manage_table.itemSelectionChanged.connect(self.concert_selected)
        
        # 自定义信号
        self.log_signal.connect(self.update_log)
        self.status_signal.connect(self.update_status)
        self.progress_signal.connect(self.update_progress)
    
    def setup_tray(self) -> None:
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/icons/app.png"))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def load_data(self) -> None:
        """加载数据"""
        # 更新抢票标签页中的演唱会列表
        self.update_concerts_table()
        
        # 更新管理标签页中的演唱会表格
        self.update_manage_table()
        
        # 加载设置
        self.load_settings()
    
    def update_concerts_table(self) -> None:
        """更新抢票标签页中的演唱会列表"""
        concerts = self.concert_model.get_all_concerts()
        self.concerts_table.setRowCount(len(concerts))
        
        for i, concert in enumerate(concerts):
            # 创建复选框单元格
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.concerts_table.setItem(i, 0, checkbox)
            
            # 设置其他单元格
            self.concerts_table.setItem(i, 1, QTableWidgetItem(concert.get("name", "")))
            self.concerts_table.setItem(i, 2, QTableWidgetItem(concert.get("date", "")))
            self.concerts_table.setItem(i, 3, QTableWidgetItem(concert.get("venue", "")))
            self.concerts_table.setItem(i, 4, QTableWidgetItem("未开始"))
    
    def update_manage_table(self) -> None:
        """更新管理标签页中的演唱会表格"""
        concerts = self.concert_model.get_all_concerts()
        self.manage_table.setRowCount(len(concerts))
        
        for i, concert in enumerate(concerts):
            self.manage_table.setItem(i, 0, QTableWidgetItem(concert.get("id", "")))
            self.manage_table.setItem(i, 1, QTableWidgetItem(concert.get("name", "")))
            self.manage_table.setItem(i, 2, QTableWidgetItem(concert.get("date", "")))
            self.manage_table.setItem(i, 3, QTableWidgetItem(concert.get("venue", "")))
            self.manage_table.setItem(i, 4, QTableWidgetItem(str(concert.get("max_price", 0))))
            
            # 创建操作按钮
            delete_btn = QPushButton("删除")
            delete_btn.setProperty("row", i)
            delete_btn.clicked.connect(self.delete_concert)
            
            self.manage_table.setCellWidget(i, 5, delete_btn)
    
    def load_settings(self) -> None:
        """加载设置"""
        # 设置刷新间隔
        refresh_interval = self.config.get("refresh_interval", 0.5)
        self.refresh_interval.setValue(refresh_interval)
        
        # 设置自动刷新
        auto_refresh = self.config.get("auto_refresh", True)
        self.auto_refresh_checkbox.setChecked(auto_refresh)
    
    @pyqtSlot()
    def start_grabbing(self) -> None:
        """开始抢票"""
        if self.is_running:
            QMessageBox.warning(self, "警告", "抢票任务已在运行中")
            return
        
        # 获取选中的演唱会
        selected_concerts = []
        for i in range(self.concerts_table.rowCount()):
            item = self.concerts_table.item(i, 0)
            if item and item.checkState() == Qt.Checked:
                concert = self.concert_model.get_concert(i)
                if concert:
                    selected_concerts.append(concert.get("id"))
        
        if not selected_concerts:
            QMessageBox.warning(self, "警告", "请选择至少一个要抢票的演唱会")
            return
        
        # 保存设置
        self.config.set("refresh_interval", self.refresh_interval.value())
        self.config.set("auto_refresh", self.auto_refresh_checkbox.isChecked())
        self.config.save()
        
        # 更新UI状态
        self.is_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # 启动Go并发抢票
        self.log_to_ui("开始抢票任务（Go 并发）")
        self.status_signal.emit("正在抢票...")
        for cid in selected_concerts:
            self._start_go_grabber(cid)
    
    def _run_grabbing_session(self, concert_ids: List[str]) -> None:
        """已由Go子进程替代。"""
        pass

    def _get_go_executable_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "go" / "ticket_grabber.exe"

    def _ensure_go_built(self) -> bool:
        exe = self._get_go_executable_path()
        if exe.exists():
            return True
        go_dir = Path(__file__).parent.parent.parent / "go"
        try:
            self.log_to_ui("正在构建Go抢票程序...")
            # 先执行 go mod tidy（忽略失败也继续）
            try:
                subprocess.run(["go", "mod", "tidy"], cwd=str(go_dir), capture_output=True, text=True, shell=False)
            except Exception:
                pass
            # 构建主程序到 go/ticket_grabber.exe
            result = subprocess.run(["go", "build", "-o", "ticket_grabber.exe", "./cmd/ticket_grabber"], cwd=str(go_dir), capture_output=True, text=True, shell=False)
            if result.stdout:
                for line in result.stdout.splitlines():
                    self.log_signal.emit(line)
            if result.stderr:
                for line in result.stderr.splitlines():
                    self.log_signal.emit(line)
            if result.returncode != 0:
                self.log_to_ui("Go 构建失败，请检查是否已安装 Go 并配置到PATH")
                return False
        except FileNotFoundError:
            self.log_to_ui("未找到 go 可执行文件，请安装 Go 并将其添加到 PATH")
            return False
        except Exception as e:
            self.log_to_ui(f"构建Go程序失败: {e}")
            return False
        return exe.exists()

    def _start_go_grabber(self, concert_id: str) -> None:
        if concert_id in self.go_processes:
            return
        if not self._ensure_go_built():
            QMessageBox.critical(self, "错误", "Go 抢票程序不存在且构建失败")
            return
        exe = str(self._get_go_executable_path())
        config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        args = [exe, "--config", str(config_path), "--concert", concert_id, "--headless"]
        try:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(Path(__file__).parent.parent.parent))
            self.go_processes[concert_id] = proc
            t = threading.Thread(target=self._stream_process_output, args=(concert_id, proc), daemon=True)
            t.start()
            self.go_threads.append(t)
            self.progress_signal.emit(50)
        except Exception as e:
            self.log_to_ui(f"启动Go进程失败[{concert_id}]: {e}")

    def _stream_process_output(self, concert_id: str, proc: subprocess.Popen) -> None:
        try:
            if not proc.stdout:
                return
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    text = line.decode(errors="ignore").rstrip()
                except Exception:
                    text = str(line).rstrip()
                self.log_signal.emit(f"[{concert_id}] {text}")
                if ("购票成功" in text) or ("支付成功" in text):
                    self.progress_signal.emit(100)
        finally:
            rc = proc.wait()
            self.log_signal.emit(f"[{concert_id}] 进程退出，代码 {rc}")
    
    @pyqtSlot()
    def stop_grabbing(self) -> None:
        """停止抢票"""
        if not self.is_running:
            return
        
        self.stopping = True
        self.log_to_ui("正在停止抢票任务...")
        self.status_signal.emit("正在停止...")
        
        # 停止所有Go子进程
        for cid, proc in list(self.go_processes.items()):
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except Exception:
                        proc.kill()
            except Exception as e:
                self.log_to_ui(f"终止进程失败[{cid}]: {e}")
            finally:
                self.go_processes.pop(cid, None)
        
        # 更新UI状态
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        self.log_to_ui("抢票任务已停止")
        self.status_signal.emit("就绪")
        self.stopping = False
    
    def _update_grabbing_progress(self) -> None:
        """更新抢票进度"""
        if not self.is_running or not self.ticket_bot:
            return
        
        # 计算进度
        if self.ticket_bot.is_ticket_found():
            progress = 100
        elif self.ticket_bot.is_running():
            progress = 50  # 正在运行
        else:
            progress = 0
            
        self.progress_signal.emit(progress)
    
    @pyqtSlot()
    def add_new_concert(self) -> None:
        """添加新演唱会"""
        # 清空编辑框
        self.concert_id_edit.setText("")
        self.concert_name_edit.setText("")
        self.concert_date_edit.setText("")
        self.concert_venue_edit.setText("")
        self.concert_url_edit.setText("")
        self.concert_price_edit.setValue(0)
        self.concert_preferences_edit.setText("")
        
        # 生成新ID
        import uuid
        new_id = str(uuid.uuid4())[:8]
        self.concert_id_edit.setText(new_id)
    
    @pyqtSlot()
    def import_concerts(self) -> None:
        """导入演唱会"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入演唱会", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    concerts = json.load(f)
                
                if isinstance(concerts, list):
                    for concert in concerts:
                        self.concert_model.add_concert(concert)
                    
                    self.update_concerts_table()
                    self.update_manage_table()
                    
                    QMessageBox.information(self, "成功", f"已导入 {len(concerts)} 个演唱会")
                else:
                    QMessageBox.warning(self, "错误", "导入文件格式不正确")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入演唱会时出错: {str(e)}")
    
    @pyqtSlot()
    def export_concerts(self) -> None:
        """导出演唱会"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出演唱会", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                import json
                concerts = self.concert_model.get_all_concerts()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(concerts, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"已导出 {len(concerts)} 个演唱会")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出演唱会时出错: {str(e)}")
    
    @pyqtSlot()
    def save_concerts(self) -> None:
        """保存演唱会更改"""
        # 获取当前编辑的演唱会信息
        concert_id = self.concert_id_edit.text().strip()
        
        if not concert_id:
            QMessageBox.warning(self, "警告", "演唱会ID不能为空")
            return
        
        concert_info = {
            "id": concert_id,
            "name": self.concert_name_edit.text().strip(),
            "date": self.concert_date_edit.text().strip(),
            "venue": self.concert_venue_edit.text().strip(),
            "url": self.concert_url_edit.text().strip(),
            "max_price": self.concert_price_edit.value(),
            "seat_preferences": [p.strip() for p in self.concert_preferences_edit.text().split(",") if p.strip()]
        }
        
        # 检查必填字段
        if not concert_info["name"]:
            QMessageBox.warning(self, "警告", "演唱会名称不能为空")
            return
            
        if not concert_info["url"]:
            QMessageBox.warning(self, "警告", "演唱会URL不能为空")
            return
            
        # 查找是否已存在该ID
        existing_index = -1
        for i, concert in enumerate(self.concert_model.concerts):
            if concert.get("id") == concert_id:
                existing_index = i
                break
        
        if existing_index >= 0:
            # 更新现有演唱会
            self.concert_model.concerts[existing_index] = concert_info
        else:
            # 添加新演唱会
            self.concert_model.add_concert(concert_info)
        
        # 保存到配置
        self.config.add_concert(concert_info)
        self.config.save()
        
        # 更新UI
        self.update_concerts_table()
        self.update_manage_table()
        
        QMessageBox.information(self, "成功", "演唱会信息已保存")
    
    @pyqtSlot()
    def delete_concert(self) -> None:
        """删除演唱会"""
        sender = self.sender()
        if not sender:
            return
            
        row = sender.property("row")
        if row is None:
            return
            
        concert = self.concert_model.get_concert(row)
        if not concert:
            return
            
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除演唱会 '{concert.get('name')}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            concert_id = concert.get("id")
            self.concert_model.remove_concert(row)
            self.config.remove_concert(concert_id)
            self.config.save()
            
            self.update_concerts_table()
            self.update_manage_table()
    
    @pyqtSlot()
    def concert_selected(self) -> None:
        """演唱会选择改变"""
        selected_rows = self.manage_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        concert = self.concert_model.get_concert(row)
        if not concert:
            return
            
        # 填充表单
        self.concert_id_edit.setText(concert.get("id", ""))
        self.concert_name_edit.setText(concert.get("name", ""))
        self.concert_date_edit.setText(concert.get("date", ""))
        self.concert_venue_edit.setText(concert.get("venue", ""))
        self.concert_url_edit.setText(concert.get("url", ""))
        self.concert_price_edit.setValue(concert.get("max_price", 0))
        
        preferences = concert.get("seat_preferences", [])
        self.concert_preferences_edit.setText(", ".join(preferences))
    
    @pyqtSlot()
    def refresh_data(self) -> None:
        """刷新数据"""
        self.concert_model.load_from_config(self.config)
        self.update_concerts_table()
        self.update_manage_table()
    
    @pyqtSlot()
    def show_settings_dialog(self) -> None:
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, parent=self)
        if dialog.exec_():
            # 设置已更改，保存配置
            self.config.save()
            # 重新加载设置
            self.load_settings()
    
    @pyqtSlot()
    def show_help(self) -> None:
        """显示帮助"""
        help_text = """
        <h3>韩国演唱会抢票系统使用指南</h3>
        
        <p><b>抢票步骤：</b></p>
        <ol>
            <li>在"演唱会管理"选项卡中添加想要抢票的演唱会</li>
            <li>在"设置"中配置账号信息和通知方式</li>
            <li>在"抢票"选项卡中选择要抢的演唱会</li>
            <li>设置刷新间隔和是否自动刷新</li>
            <li>点击"开始抢票"按钮开始抢票</li>
        </ol>
        
        <p><b>注意事项：</b></p>
        <ul>
            <li>请确保网络连接稳定</li>
            <li>建议使用代理以避免IP被封</li>
            <li>成功抢到票后会通过设置的通知方式通知您</li>
            <li>可以最小化程序到系统托盘继续运行</li>
        </ul>
        """
        
        QMessageBox.information(self, "帮助", help_text)
    
    @pyqtSlot()
    def clear_log(self) -> None:
        """清除日志"""
        self.log_text.clear()
    
    @pyqtSlot()
    def save_log(self) -> None:
        """保存日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                
                QMessageBox.information(self, "成功", "日志已保存")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志时出错: {str(e)}")
    
    def log_to_ui(self, message: str) -> None:
        """将日志消息发送到UI"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_signal.emit(f"{timestamp} - {message}")
    
    @pyqtSlot(str)
    def update_log(self, message: str) -> None:
        """更新日志显示"""
        self.log_text.appendPlainText(message)
        self.log_text.moveCursor(QTextCursor.End)
    
    @pyqtSlot(str)
    def update_status(self, message: str) -> None:
        """更新状态栏"""
        self.statusbar.showMessage(message)
    
    @pyqtSlot(int)
    def update_progress(self, value: int) -> None:
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """处理系统托盘激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """处理窗口关闭事件"""
        if self.is_running:
            reply = QMessageBox.question(
                self,
                "确认",
                "抢票任务正在运行，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
                
            # 停止抢票
            self.stop_grabbing()
        
        # 隐藏到系统托盘而不是直接退出
        event.ignore()
        self.hide()
        
        # 显示通知
        self.tray_icon.showMessage(
            "韩国演唱会抢票系统",
            "程序已最小化到系统托盘，右键点击图标可退出",
            QSystemTrayIcon.Information,
            2000
        )
    
    def close_application(self) -> None:
        """完全关闭应用程序"""
        # 停止抢票
        if self.is_running:
            self.stop_grabbing()
        
        # 保存配置
        self.config.save()
        
        # 退出应用
        QApplication.quit()

# 应用程序入口
def run_app():
    """运行应用程序"""
    app = QApplication(sys.argv)
    app.setApplicationName("韩国演唱会抢票系统")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口时不退出应用
    
    # 设置样式表
    # with open("python/ui/resources/style.qss", "r") as f:
    #     app.setStyleSheet(f.read())
    
    # 加载资源
    # import python.ui.resources.resources_rc
    
    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()