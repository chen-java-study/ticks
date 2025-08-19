"""
韩国演唱会抢票系统 - Python模块包

此包包含抢票系统的所有Python代码，组织为以下子模块：
- core: 抢票核心逻辑
- ui: 用户界面
- utils: 工具类
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# 导出关键类，方便直接从包导入
from python.core.ticket_bot import TicketBot
from python.ui.main_window import MainWindow