"""
抢票机器人核心模块
"""

import time
import random
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable

# Selenium相关导入
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 项目模块导入
from python.utils.config_manager import ConfigManager
from python.utils.logger import LoggerMixin
from python.utils.notification import NotificationManager
from python.core.api_client import APIClient, InterParkClient, Yes24Client, MelonClient
from python.core.captcha_solver import CaptchaSolver

class TicketBot(LoggerMixin):
    """抢票机器人核心类"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化抢票机器人
        
        Args:
            config_manager: 配置管理器实例
        """
        self.setup_logger()
        self.config = config_manager
        self.notification = NotificationManager(config_manager)
        
        self.driver = None
        self.api_client = None
        self.captcha_solver = None
        
        self.is_running = False
        self.stop_flag = threading.Event()
        self.ticket_found = threading.Event()
        
        self.logger.info("抢票机器人已初始化")
    
    def setup_browser(self) -> bool:
        """
        设置浏览器
        
        Returns:
            是否设置成功
        """
        try:
            # 创建Chrome选项
            chrome_options = Options()
            
            # 根据配置设置无头模式
            if self.config.get("browser.headless", False):
                self.logger.info("启用无头模式")
                chrome_options.add_argument("--headless=new")
            
            # 设置用户代理
            user_agent = self.config.get("browser.user_agent", "")
            if user_agent:
                chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # 添加其他选项
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--start-maximized")
            
            # 如果有代理配置，添加代理
            proxy = self.config.get("proxy", "")
            if proxy:
                self.logger.info(f"使用代理: {proxy}")
                chrome_options.add_argument(f"--proxy-server={proxy}")
            
            # 使用WebDriver Manager自动下载合适的驱动
            self.logger.info("正在启动浏览器...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            
            # 初始化验证码处理器
            self.captcha_solver = CaptchaSolver(self.config)
            
            self.logger.info("浏览器设置成功")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器设置失败: {str(e)}")
            return False
    
    def setup_api_client(self, site: str) -> bool:
        """
        设置API客户端
        
        Args:
            site: 票务网站名称
            
        Returns:
            是否设置成功
        """
        try:
            if site.lower() == "interpark":
                self.api_client = InterParkClient()
            elif site.lower() == "yes24":
                self.api_client = Yes24Client()
            elif site.lower() == "melon":
                self.api_client = MelonClient()
            else:
                self.logger.error(f"不支持的票务网站: {site}")
                return False
            
            self.logger.info(f"API客户端设置成功: {site}")
            return True
            
        except Exception as e:
            self.logger.error(f"API客户端设置失败: {str(e)}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        登录到票务网站
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否登录成功
        """
        if not self.api_client:
            self.logger.error("API客户端未初始化")
            return False
        
        try:
            self.logger.info("正在登录...")
            success = self.api_client.login(username, password)
            
            if success:
                self.logger.info("登录成功")
            else:
                self.logger.error("登录失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"登录过程中发生错误: {str(e)}")
            return False
    
    def start_grabbing(self, concert_info: Dict[str, Any]) -> None:
        """
        开始抢票
        
        Args:
            concert_info: 演唱会信息
        """
        if self.is_running:
            self.logger.warning("抢票机器人已在运行中")
            return
        
        self.is_running = True
        self.stop_flag.clear()
        self.ticket_found.clear()
        
        # 创建抢票线程
        grab_thread = threading.Thread(
            target=self._grabbing_worker,
            args=(concert_info,),
            daemon=True
        )
        grab_thread.start()
        
        self.logger.info(f"开始抢票: {concert_info.get('name', '未知演唱会')}")
    
    def stop_grabbing(self) -> None:
        """停止抢票"""
        if not self.is_running:
            return
        
        self.logger.info("正在停止抢票...")
        self.stop_flag.set()
        self.is_running = False
        
        # 关闭浏览器
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"关闭浏览器时发生错误: {str(e)}")
            finally:
                self.driver = None
        
        self.logger.info("抢票已停止")
    
    def _grabbing_worker(self, concert_info: Dict[str, Any]) -> None:
        """
        抢票工作线程
        
        Args:
            concert_info: 演唱会信息
        """
        try:
            # 设置浏览器
            if not self.setup_browser():
                self.logger.error("浏览器设置失败")
                return
            
            # 设置API客户端
            site = concert_info.get("site", "interpark")
            if not self.setup_api_client(site):
                self.logger.error("API客户端设置失败")
                return
            
            # 登录
            username = self.config.get("user.username", "")
            password = self.config.get("user.password", "")
            
            if not username or not password:
                self.logger.error("用户名或密码未设置")
                return
            
            if not self.login(username, password):
                self.logger.error("登录失败")
                return
            
            # 开始抢票循环
            self._grabbing_loop(concert_info)
            
        except Exception as e:
            self.logger.error(f"抢票过程中发生错误: {str(e)}")
        finally:
            self.is_running = False
    
    def _grabbing_loop(self, concert_info: Dict[str, Any]) -> None:
        """
        抢票主循环
        
        Args:
            concert_info: 演唱会信息
        """
        refresh_interval = self.config.get("ticketing.refresh_interval", 0.5)
        max_retries = self.config.get("ticketing.max_retries", 3)
        retry_delay = self.config.get("ticketing.retry_delay", 1.0)
        
        attempt_count = 0
        
        while not self.stop_flag.is_set():
            attempt_count += 1
            self.logger.info(f"抢票尝试 #{attempt_count}")
            
            try:
                # 获取可用座位
                concert_id = concert_info.get("id", "")
                available_seats = self.api_client.get_available_seats(concert_id)
                
                if available_seats:
                    self.logger.info(f"找到 {len(available_seats)} 个可用座位")
                    
                    # 筛选符合条件的座位
                    suitable_seats = self._filter_seats(available_seats, concert_info)
                    
                    if suitable_seats:
                        # 尝试预订
                        if self._try_book_seat(suitable_seats[0], concert_info):
                            self.ticket_found.set()
                            break
                else:
                    self.logger.info("当前没有可用座位")
                
                # 等待下次尝试
                if not self.stop_flag.is_set():
                    time.sleep(refresh_interval)
                    
            except Exception as e:
                self.logger.error(f"抢票尝试 #{attempt_count} 失败: {str(e)}")
                
                if attempt_count >= max_retries:
                    self.logger.error("达到最大重试次数，停止抢票")
                    break
                
                time.sleep(retry_delay)
    
    def _filter_seats(self, seats: List[Dict[str, Any]], concert_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        筛选符合条件的座位
        
        Args:
            seats: 可用座位列表
            concert_info: 演唱会信息
            
        Returns:
            符合条件的座位列表
        """
        max_price = concert_info.get("max_price", 0)
        preferred_seats = concert_info.get("preferred_seats", [])
        
        filtered_seats = []
        
        for seat in seats:
            # 价格过滤
            seat_price = seat.get("price", 0)
            if max_price > 0 and seat_price > max_price:
                continue
            
            # 座位类型过滤
            seat_type = seat.get("type", "")
            if preferred_seats and seat_type not in preferred_seats:
                continue
            
            filtered_seats.append(seat)
        
        # 按价格排序
        filtered_seats.sort(key=lambda x: x.get("price", 0))
        
        return filtered_seats
    
    def _try_book_seat(self, seat: Dict[str, Any], concert_info: Dict[str, Any]) -> bool:
        """
        尝试预订座位
        
        Args:
            seat: 座位信息
            concert_info: 演唱会信息
            
        Returns:
            是否预订成功
        """
        try:
            self.logger.info(f"尝试预订座位: {seat.get('type', '未知')}")
            
            # 通知发现可用票
            self.notification.notify_ticket_found(concert_info, seat)
            
            # 尝试预订
            success = self.api_client.book_seat(seat)
            
            if success:
                self.logger.info("预订成功！")
                
                # 获取订单信息
                order_info = self.api_client.get_order_info()
                
                # 通知购票成功
                self.notification.notify_purchase_success(concert_info, order_info)
                
                return True
            else:
                self.logger.warning("预订失败")
                return False
                
        except Exception as e:
            self.logger.error(f"预订过程中发生错误: {str(e)}")
            return False
    
    def is_running(self) -> bool:
        """
        检查是否正在运行
        
        Returns:
            是否正在运行
        """
        return self.is_running
    
    def is_ticket_found(self) -> bool:
        """
        检查是否找到票
        
        Returns:
            是否找到票
        """
        return self.ticket_found.is_set()