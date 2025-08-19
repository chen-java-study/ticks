#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
韩国演唱会抢票系统演示脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from python.utils.config_manager import ConfigManager
from python.utils.logger import setup_logger
from python.core.ticket_bot import TicketBot

def demo_config():
    """演示配置管理功能"""
    print("=" * 50)
    print("配置管理演示")
    print("=" * 50)
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 显示应用信息
    app_name = config.get("app.name", "未知")
    app_version = config.get("app.version", "未知")
    print(f"应用名称: {app_name}")
    print(f"应用版本: {app_version}")
    
    # 显示支持的票务网站
    sites = config.get("ticketing.sites", {})
    print(f"\n支持的票务网站:")
    for site_id, site_info in sites.items():
        print(f"  - {site_info.get('name', site_id)}: {site_info.get('url', '未知URL')}")
    
    # 显示演唱会列表
    concerts = config.get_all_concerts()
    print(f"\n配置的演唱会 ({len(concerts)} 个):")
    for i, concert in enumerate(concerts, 1):
        print(f"  {i}. {concert.get('name', '未知')}")
        print(f"     艺术家: {concert.get('artist', '未知')}")
        print(f"     场馆: {concert.get('venue', '未知')}")
        print(f"     日期: {concert.get('date', '未知')}")
        print(f"     票务网站: {concert.get('site', '未知')}")
        print()

def demo_logger():
    """演示日志系统"""
    print("=" * 50)
    print("日志系统演示")
    print("=" * 50)
    
    # 设置日志
    logger = setup_logger()
    
    # 记录不同类型的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    
    print("日志已记录到 logs/ 目录")

def demo_ticket_bot():
    """演示抢票机器人"""
    print("=" * 50)
    print("抢票机器人演示")
    print("=" * 50)
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 创建抢票机器人
    bot = TicketBot(config)
    
    print("抢票机器人已创建")
    print(f"运行状态: {'运行中' if bot.is_running() else '未运行'}")
    print(f"找到票: {'是' if bot.is_ticket_found() else '否'}")
    
    # 显示机器人配置
    print(f"\n机器人配置:")
    print(f"  浏览器无头模式: {config.get('browser.headless', False)}")
    print(f"  自动刷新: {config.get('ticketing.auto_refresh', True)}")
    print(f"  刷新间隔: {config.get('ticketing.refresh_interval', 0.5)}秒")
    print(f"  最大重试次数: {config.get('ticketing.max_retries', 3)}")

def demo_api_clients():
    """演示API客户端"""
    print("=" * 50)
    print("API客户端演示")
    print("=" * 50)
    
    from python.core.api_client import InterParkClient, Yes24Client, MelonClient
    
    # 创建不同网站的客户端
    clients = {
        "Interpark": InterParkClient(),
        "Yes24": Yes24Client(),
        "Melon Ticket": MelonClient()
    }
    
    for name, client in clients.items():
        print(f"{name} 客户端:")
        print(f"  基础URL: {client.base_url}")
        print(f"  用户代理: {client.session.headers.get('User-Agent', '未设置')[:50]}...")
        print()

def main():
    """主演示函数"""
    print("🎫 韩国演唱会抢票系统演示")
    print("=" * 60)
    
    try:
        # 演示各个功能模块
        demo_config()
        demo_logger()
        demo_ticket_bot()
        demo_api_clients()
        
        print("=" * 60)
        print("✅ 演示完成！")
        print("\n系统功能包括:")
        print("  📋 配置管理 - 支持多票务网站配置")
        print("  📝 日志系统 - 完整的日志记录和监控")
        print("  🤖 抢票机器人 - 自动化抢票流程")
        print("  🌐 API客户端 - 支持Interpark、Yes24、Melon Ticket")
        print("  🖥️ 图形界面 - 友好的用户界面")
        print("  📧 通知系统 - 邮件、Telegram、桌面通知")
        print("  🔐 验证码识别 - 自动处理验证码")
        
        print("\n使用方法:")
        print("  1. 运行 setup.bat 设置环境")
        print("  2. 编辑 config/config.json 配置账号和演唱会")
        print("  3. 运行 start.bat 启动程序")
        print("  4. 或运行 python run.py --headless --concert concert_id")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
