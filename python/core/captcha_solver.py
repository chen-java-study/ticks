"""
验证码处理模块，用于自动识别和处理各类验证码
"""

import os
import base64
import time
import tempfile
from typing import Dict, Any, Optional, Union, Tuple
import io
import json
import requests
from pathlib import Path
import random

import cv2
import numpy as np
from PIL import Image
import pytesseract

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from python.utils.config_manager import ConfigManager
from python.utils.logger import LoggerMixin

class CaptchaSolver(LoggerMixin):
    """验证码处理类，支持图片验证码和滑动验证码"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化验证码处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.setup_logger()
        self.config = config_manager
        
        # 配置pytesseract路径
        pytesseract_path = self.config.get("captcha.pytesseract_path", "")
        if pytesseract_path:
            pytesseract.pytesseract.tesseract_cmd = pytesseract_path
            
        self.logger.info("验证码处理模块已初始化")
    
    def solve_captcha(self, driver: WebDriver, captcha_type: str = "auto") -> bool:
        """
        解决验证码
        
        Args:
            driver: Selenium WebDriver实例
            captcha_type: 验证码类型，可以是 "image", "slider", "audio" 或 "auto"
            
        Returns:
            是否成功解决
        """
        self.logger.info(f"开始处理验证码，类型: {captcha_type}")
        
        if captcha_type == "auto":
            # 自动检测验证码类型
            captcha_type = self._detect_captcha_type(driver)
            self.logger.info(f"检测到验证码类型: {captcha_type}")
        
        try:
            if captcha_type == "image":
                return self._solve_image_captcha(driver)
            elif captcha_type == "slider":
                return self._solve_slider_captcha(driver)
            elif captcha_type == "audio":
                return self._solve_audio_captcha(driver)
            else:
                self.logger.error(f"不支持的验证码类型: {captcha_type}")
                return False
        except Exception as e:
            self.logger.error(f"处理验证码时发生错误: {str(e)}")
            return False
    
    def _detect_captcha_type(self, driver: WebDriver) -> str:
        """
        检测页面中的验证码类型
        
        Args:
            driver: Selenium WebDriver实例
            
        Returns:
            验证码类型: "image", "slider", "audio" 或 "unknown"
        """
        # 检查是否有图片验证码
        image_captcha_selectors = [
            "img[alt*='captcha']", 
            "img[src*='captcha']",
            "img.captcha",
            ".captcha img",
            "#captchaImage"
        ]
        
        for selector in image_captcha_selectors:
            if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                return "image"
        
        # 检查是否有滑动验证码
        slider_captcha_selectors = [
            ".slider-captcha",
            ".captcha-slider",
            ".geetest_slider",
            ".sliderContainer"
        ]
        
        for selector in slider_captcha_selectors:
            if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                return "slider"
        
        # 检查是否有音频验证码
        audio_captcha_selectors = [
            "audio[src*='captcha']",
            ".audio-captcha",
            "a[href*='audio']"
        ]
        
        for selector in audio_captcha_selectors:
            if len(driver.find_elements(By.CSS_SELECTOR, selector)) > 0:
                return "audio"
                
        return "unknown"
    
    def _solve_image_captcha(self, driver: WebDriver) -> bool:
        """
        解决图片验证码
        
        Args:
            driver: Selenium WebDriver实例
            
        Returns:
            是否成功解决
        """
        # 查找验证码图片元素
        captcha_selectors = [
            "img[alt*='captcha']", 
            "img[src*='captcha']",
            "img.captcha",
            ".captcha img",
            "#captchaImage"
        ]
        
        captcha_img = None
        for selector in captcha_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                captcha_img = elements[0]
                break
        
        if not captcha_img:
            self.logger.error("未找到验证码图片元素")
            return False
        
        # 获取验证码图片数据
        captcha_base64 = self._get_image_base64(captcha_img)
        if not captcha_base64:
            self.logger.error("无法获取验证码图片数据")
            return False
            
        # 解析验证码
        captcha_text = self._recognize_captcha(captcha_base64)
        if not captcha_text:
            self.logger.error("验证码识别失败")
            return False
            
        self.logger.info(f"验证码识别结果: {captcha_text}")
        
        # 查找验证码输入框
        input_selectors = [
            "input[name*='captcha']",
            "input[id*='captcha']",
            "input.captcha",
            "#captchaInput",
            ".captcha input"
        ]
        
        captcha_input = None
        for selector in input_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                captcha_input = elements[0]
                break
        
        if not captcha_input:
            self.logger.error("未找到验证码输入框")
            return False
            
        # 输入验证码
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        
        # 查找提交按钮
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            ".captcha-submit",
            "#loginBtn",
            ".login-button"
        ]
        
        submit_button = None
        for selector in submit_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                submit_button = elements[0]
                break
        
        if submit_button:
            submit_button.click()
        else:
            # 如果找不到提交按钮，尝试按回车键
            captcha_input.send_keys("\n")
            
        # 等待页面加载
        time.sleep(2)
        
        # 检查是否成功
        error_selectors = [
            ".captcha-error",
            ".error-message",
            "#errorMsg",
            ".alert-danger"
        ]
        
        for selector in error_selectors:
            errors = driver.find_elements(By.CSS_SELECTOR, selector)
            if errors and errors[0].is_displayed():
                self.logger.warning(f"验证码输入后出现错误: {errors[0].text}")
                return False
                
        return True
    
    def _solve_slider_captcha(self, driver: WebDriver) -> bool:
        """
        解决滑动验证码
        
        Args:
            driver: Selenium WebDriver实例
            
        Returns:
            是否成功解决
        """
        from selenium.webdriver import ActionChains
        
        # 查找滑块元素
        slider_selectors = [
            ".slider-button",
            ".geetest_slider_button",
            ".handler",
            ".sliderContainer .slider"
        ]
        
        slider = None
        for selector in slider_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].is_displayed():
                slider = elements[0]
                break
        
        if not slider:
            self.logger.error("未找到滑块元素")
            return False
            
        # 查找背景图片和缺口图片
        background_selectors = [
            ".captcha-bg",
            ".geetest_canvas_bg",
            ".sliderContainer .bg"
        ]
        
        # 这里实际情况可能需要截取整个区域的屏幕截图
        # 并通过图像处理找到缺口位置
        # 以下为简化实现，实际应用可能需要更复杂的图像处理
        
        # 获取滑动距离
        # 这里使用随机值作为示例，实际应该通过图像处理计算
        width = slider.size['width']
        track = self._get_slide_track(random.randint(50, 150))
        
        # 执行滑动
        action = ActionChains(driver)
        action.click_and_hold(slider).perform()
        
        for x in track:
            action.move_by_offset(x, 0).perform()
            
        # 添加随机释放停顿，模拟人类行为
        time.sleep(0.5)
        action.release().perform()
        
        # 等待验证结果
        time.sleep(2)
        
        # 检查是否成功
        success_selectors = [
            ".captcha-success",
            ".geetest_success"
        ]
        
        for selector in success_selectors:
            success = driver.find_elements(By.CSS_SELECTOR, selector)
            if success and success[0].is_displayed():
                self.logger.info("滑动验证码解决成功")
                return True
                
        error_selectors = [
            ".captcha-error",
            ".geetest_error"
        ]
        
        for selector in error_selectors:
            errors = driver.find_elements(By.CSS_SELECTOR, selector)
            if errors and errors[0].is_displayed():
                self.logger.warning(f"滑动验证码解决失败: {errors[0].text}")
                return False
        
        # 没有明确成功/失败提示，假设成功
        return True
    
    def _solve_audio_captcha(self, driver: WebDriver) -> bool:
        """
        解决音频验证码
        
        Args:
            driver: Selenium WebDriver实例
            
        Returns:
            是否成功解决
        """
        # 音频验证码需要更复杂的语音识别技术
        # 实际项目中可能需要接入专业的语音识别API
        self.logger.warning("音频验证码处理未实现")
        return False
    
    def _get_image_base64(self, img_element) -> str:
        """
        获取图片元素的Base64数据
        
        Args:
            img_element: 图片元素
            
        Returns:
            Base64编码的图片数据
        """
        try:
            # 首先尝试直接从src属性获取
            src = img_element.get_attribute('src')
            if src.startswith('data:image'):
                # 提取Base64部分
                return src.split(',')[1]
            
            # 如果src是URL，尝试截图
            img_element.screenshot(os.path.join(tempfile.gettempdir(), 'captcha.png'))
            
            # 读取截图并转为Base64
            with open(os.path.join(tempfile.gettempdir(), 'captcha.png'), 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"获取验证码图片失败: {str(e)}")
            return ""
    
    def _recognize_captcha(self, image_base64: str) -> str:
        """
        识别验证码
        
        Args:
            image_base64: Base64编码的图片数据
            
        Returns:
            识别出的验证码文本
        """
        # 首先尝试使用OCR
        result = self._recognize_with_ocr(image_base64)
        
        # 如果OCR失败，尝试使用外部API
        if not result:
            result = self._recognize_with_api(image_base64)
        
        return result
    
    def _recognize_with_ocr(self, image_base64: str) -> str:
        """
        使用OCR识别验证码
        
        Args:
            image_base64: Base64编码的图片数据
            
        Returns:
            识别出的验证码文本
        """
        try:
            # 将Base64转换为图片
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # 图像预处理
            # 转为灰度图
            image = image.convert('L')
            
            # 二值化处理
            threshold = 150
            table = []
            for i in range(256):
                if i < threshold:
                    table.append(0)
                else:
                    table.append(1)
            
            image = image.point(table, '1')
            
            # 保存预处理后的图片
            preprocessed_path = os.path.join(tempfile.gettempdir(), 'captcha_preprocessed.png')
            image.save(preprocessed_path)
            
            # 识别文本
            config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            text = pytesseract.image_to_string(image, config=config)
            
            # 清理结果
            text = text.strip()
            
            self.logger.debug(f"OCR识别结果: '{text}'")
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR识别验证码失败: {str(e)}")
            return ""
    
    def _recognize_with_api(self, image_base64: str) -> str:
        """
        使用外部API识别验证码
        
        Args:
            image_base64: Base64编码的图片数据
            
        Returns:
            识别出的验证码文本
        """
        # 检查API配置
        api_key = self.config.get("captcha.api_key", "")
        api_url = self.config.get("captcha.api_url", "")
        
        if not api_key or not api_url:
            self.logger.warning("验证码API配置不完整，无法使用外部API识别")
            return ""
            
        try:
            # 调用验证码识别API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "image": image_base64,
                "options": {
                    "language": "eng",
                    "case": "mixed"
                }
            }
            
            response = requests.post(api_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                self.logger.info(f"API识别结果: '{text}'")
                return text
            else:
                self.logger.error(f"API请求失败: {response.status_code} {response.text}")
                return ""
                
        except Exception as e:
            self.logger.error(f"调用验证码API失败: {str(e)}")
            return ""
    
    def _get_slide_track(self, distance: int) -> list:
        """
        生成滑动轨迹
        
        Args:
            distance: 滑动距离
            
        Returns:
            滑动轨迹列表
        """
        # 模拟人类滑动特征的轨迹生成算法
        tracks = []
        current = 0
        mid = distance * 3 / 4
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
                
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1/2 * a * t * t
            current += move
            tracks.append(round(move))
            
        # 校准，确保刚好滑到终点
        total = sum(tracks)
        if total > distance:
            tracks[-1] -= (total - distance)
        elif total < distance:
            tracks.append(distance - total)
            
        return tracks