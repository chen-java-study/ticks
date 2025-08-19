#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
韩国演唱会抢票系统 - 主入口文件

此文件是应用程序的入口点，负责初始化日志、配置和UI。
"""

import sys
import os
import logging
from pathlib import Path
import argparse

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 导入项目模块
from python.utils.logger import setup_logger
from python.ui.main_window import MainWindow
from python.utils.config_manager import ConfigManager
from python.core.ticket_bot import TicketBot

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="韩国演唱会抢票系统")
    parser.add_argument("--headless", action="store_true", help="无界面模式，不显示GUI")
    parser.add_argument("--concert", type=str, help="指定要抢票的演唱会ID")
    parser.add_argument("--config", type=str, default="config/config.json", 
                      help="指定配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    return parser.parse_args()

def run_headless(args, config_manager):
    """运行无界面模式"""
    print("正在以无界面模式运行...")
    
    # 获取指定演唱会信息
    concert_id = args.concert
    if not concert_id:
        print("错误: 无界面模式必须指定演唱会ID (--concert)")
        sys.exit(1)
        
    # 获取所有演唱会
    concerts = config_manager.get_all_concerts()
    target_concert = None
    
    for concert in concerts:
        if concert.get('id') == concert_id:
            target_concert = concert
            break
    
    if not target_concert:
        print(f"错误: 找不到ID为'{concert_id}'的演唱会")
        sys.exit(1)
    
    # 创建抢票机器人并开始抢票
    bot = TicketBot(config_manager)
    bot.start_grabbing(target_concert)

def run_gui():
    """运行GUI界面"""
    from PyQt5.QtWidgets import QApplication
    
    # 创建QT应用
    app = QApplication(sys.argv)
    app.setApplicationName("韩国演唱会抢票助手")
    
    # 加载样式表
    style_file = Path(project_root) / "python" / "ui" / "resources" / "style.qss"
    if style_file.exists():
        with open(style_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 执行应用程序
    sys.exit(app.exec_())

def main():
    """程序主入口点"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    
    # 初始化配置
    try:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = Path(project_root) / args.config
            
        config_manager = ConfigManager(str(config_path))
        logger.info(f"配置已加载: {config_path}")
    except Exception as e:
        logger.error(f"配置加载失败: {str(e)}")
        sys.exit(1)
    
    # 根据模式选择运行方式
    if args.headless:
        run_headless(args, config_manager)
    else:
        run_gui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序发生未处理的异常: {str(e)}")
        # 在调试模式下重新抛出异常以查看堆栈跟踪
        if "--debug" in sys.argv:
            raise
        sys.exit(1)