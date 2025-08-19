"""
通知模块，提供各种通知方式
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime

from python.utils.config_manager import ConfigManager
from python.utils.logger import LoggerMixin

class NotificationManager(LoggerMixin):
    """通知管理器，支持多种通知方式"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化通知管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.setup_logger()
        self.config = config_manager
        self.logger.info("通知管理器已初始化")
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         notification_types: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_types: 通知类型列表，如 ["email", "telegram"]，默认使用所有启用的通知
            
        Returns:
            各通知类型的发送结果字典
        """
        results = {}
        
        # 如果未指定通知类型，则使用所有已启用的通知
        if notification_types is None:
            notification_types = []
            if self.config.get("notification.email.enabled", False):
                notification_types.append("email")
            if self.config.get("notification.telegram.enabled", False):
                notification_types.append("telegram")
        
        # 发送每种类型的通知
        for notify_type in notification_types:
            if notify_type == "email":
                results["email"] = self.send_email(title, message)
            elif notify_type == "telegram":
                results["telegram"] = self.send_telegram(title, message)
            else:
                self.logger.warning(f"未知的通知类型: {notify_type}")
                results[notify_type] = False
        
        return results
    
    def send_email(self, subject: str, body: str) -> bool:
        """
        发送电子邮件通知
        
        Args:
            subject: 邮件主题
            body: 邮件内容
            
        Returns:
            是否发送成功
        """
        # 检查是否启用
        if not self.config.get("notification.email.enabled", False):
            self.logger.info("邮件通知未启用")
            return False
        
        # 获取邮件配置
        smtp_server = self.config.get("notification.email.smtp_server", "")
        smtp_port = self.config.get("notification.email.smtp_port", 587)
        sender = self.config.get("notification.email.sender", "")
        password = self.config.get("notification.email.password", "")
        recipient = self.config.get("notification.email.recipient", "")
        
        # 验证必要的配置
        if not all([smtp_server, sender, password, recipient]):
            self.logger.error("邮件配置不完整")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = f"[抢票通知] {subject}"
            
            # 添加正文
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            email_body = f"{body}\n\n发送时间: {timestamp}"
            msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
            
            # 连接到SMTP服务器并发送
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # 启用TLS加密
                server.login(sender, password)
                server.send_message(msg)
            
            self.logger.info(f"邮件通知已发送至 {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return False
    
    def send_telegram(self, title: str, message: str) -> bool:
        """
        发送Telegram通知
        
        Args:
            title: 通知标题
            message: 通知内容
            
        Returns:
            是否发送成功
        """
        # 检查是否启用
        if not self.config.get("notification.telegram.enabled", False):
            self.logger.info("Telegram通知未启用")
            return False
        
        # 获取Telegram配置
        bot_token = self.config.get("notification.telegram.bot_token", "")
        chat_id = self.config.get("notification.telegram.chat_id", "")
        
        # 验证必要的配置
        if not bot_token or not chat_id:
            self.logger.error("Telegram配置不完整")
            return False
        
        try:
            # 构建消息
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            telegram_message = f"*{title}*\n\n{message}\n\n发送时间: {timestamp}"
            
            # 发送请求
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": telegram_message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Telegram通知已发送")
                return True
            else:
                self.logger.error(f"发送Telegram通知失败: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"发送Telegram通知失败: {str(e)}")
            return False
    
    def notify_ticket_found(self, concert_info: Dict[str, Any], seat_info: Dict[str, Any]) -> None:
        """
        发现可购票通知
        
        Args:
            concert_info: 演唱会信息
            seat_info: 座位信息
        """
        title = f"发现可购票: {concert_info.get('name', '未知演唱会')}"
        message = (
            f"发现可购票的演唱会!\n\n"
            f"名称: {concert_info.get('name', '未知')}\n"
            f"日期: {concert_info.get('date', '未知')}\n"
            f"场馆: {concert_info.get('venue', '未知')}\n"
            f"座位类型: {seat_info.get('type', '未知')}\n"
            f"价格: {seat_info.get('price', '未知')}\n\n"
            f"请立即访问: {concert_info.get('url', '')}"
        )
        
        self.send_notification(title, message)
    
    def notify_purchase_success(self, concert_info: Dict[str, Any], order_info: Dict[str, Any]) -> None:
        """
        购票成功通知
        
        Args:
            concert_info: 演唱会信息
            order_info: 订单信息
        """
        title = f"购票成功: {concert_info.get('name', '未知演唱会')}"
        message = (
            f"恭喜！演唱会门票购买成功!\n\n"
            f"名称: {concert_info.get('name', '未知')}\n"
            f"日期: {concert_info.get('date', '未知')}\n"
            f"场馆: {concert_info.get('venue', '未知')}\n"
            f"座位: {order_info.get('seat_type', '未知')}\n"
            f"订单号: {order_info.get('order_id', '未知')}\n"
            f"价格: {order_info.get('price', '未知')}\n\n"
            f"支付截止时间: {order_info.get('payment_deadline', '未知')}\n"
            f"查看订单: {order_info.get('order_url', '')}"
        )
        
        self.send_notification(title, message)
    
    def notify_error(self, error_message: str, error_details: Optional[str] = None) -> None:
        """
        发送错误通知
        
        Args:
            error_message: 错误消息
            error_details: 错误详情
        """
        title = f"抢票系统错误"
        message = f"抢票过程中发生错误: {error_message}"
        
        if error_details:
            message += f"\n\n详细信息:\n{error_details}"
        
        self.send_notification(title, message)