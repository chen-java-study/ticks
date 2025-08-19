"""
日志管理模块，提供日志记录功能
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(log_level: int = logging.INFO, 
                log_file: Optional[str] = None) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别，默认为 INFO
        log_file: 日志文件路径，如果为None，则自动生成
        
    Returns:
        日志记录器实例
    """
    # 创建日志目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"ticket_bot_{timestamp}.log"
    else:
        log_file = Path(log_file)
        if not log_file.is_absolute():
            log_file = log_dir / log_file
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 记录初始信息
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    logger.info(f"日志级别: {logging.getLevelName(log_level)}")
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为模块名
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    可混入类，为其他类提供日志功能
    
    用法:
    ```python
    class MyClass(LoggerMixin):
        def __init__(self):
            self.setup_logger()
            self.logger.info("初始化完成")
    ```
    """
    
    def setup_logger(self, name: Optional[str] = None) -> None:
        """
        设置实例日志记录器
        
        Args:
            name: 日志记录器名称，默认为类名
        """
        if name is None:
            name = self.__class__.__name__
        self.logger = get_logger(name)