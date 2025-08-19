"""
配置管理模块，负责读写配置文件
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

class ConfigManager:
    """配置管理类，负责读写配置文件"""
    
    def __init__(self, config_path: str = "config/config.json", 
                default_config_path: str = "config/default_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            default_config_path: 默认配置文件路径
        """
        # 解析路径
        self.config_path = self._resolve_path(config_path)
        self.default_config_path = self._resolve_path(default_config_path)
        
        # 加载配置
        self.config = self._load_config()
        
        # 设置默认配置
        self._set_defaults()
        
    def _resolve_path(self, path: str) -> str:
        """解析路径，支持相对路径和绝对路径"""
        p = Path(path)
        if p.is_absolute():
            return str(p)
        else:
            # 相对于项目根目录
            root_dir = Path(__file__).parent.parent.parent.absolute()
            return str(root_dir / p)
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 先尝试加载默认配置
            default_config = {}
            if os.path.exists(self.default_config_path):
                with open(self.default_config_path, 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
                    logging.info(f"已加载默认配置文件: {self.default_config_path}")
            
            # 再加载用户配置
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    logging.info(f"已加载用户配置文件: {self.config_path}")
                    
                    # 合并默认配置和用户配置
                    self._merge_configs(default_config, user_config)
                    return default_config
            else:
                logging.info(f"用户配置文件 {self.config_path} 不存在，将使用默认配置")
                return default_config
                
        except Exception as e:
            logging.error(f"加载配置文件出错: {str(e)}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """递归合并配置字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 如果两边都是字典，递归合并
                self._merge_configs(base[key], value)
            else:
                # 否则覆盖
                base[key] = value
    
    def _set_defaults(self) -> None:
        """设置默认配置项"""
        defaults = {
            "username": "",
            "password": "",
            "ticketing_site": "interpark",  # 默认为Interpark票务网站
            "auto_refresh": True,
            "refresh_interval": 0.5,  # 刷新间隔(秒)
            "max_price": 0,  # 0表示不限制价格
            "preferred_seats": [],
            "proxy": "",
            "notification": {
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "sender": "",
                    "password": "",
                    "recipient": ""
                },
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_id": ""
                }
            },
            "browser": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "headless": False
            },
            "sites": {
                "interpark": {
                    "login_url": "https://ticket.interpark.com/Gate/TPLogin.asp",
                    "search_url": "https://tickets.interpark.com/search"
                },
                "yes24": {
                    "login_url": "https://www.yes24.com/Templates/FTLogin.aspx",
                    "search_url": "https://ticket.yes24.com/New/Search.aspx"
                },
                "melon": {
                    "login_url": "https://member.melon.com/muid/login/web/login_inform.htm",
                    "search_url": "https://ticket.melon.com/search/index.htm"
                }
            },
            "concerts": []
        }
        
        # 更新缺失的配置项
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                # 递归处理嵌套字典
                for sub_key, sub_value in value.items():
                    if sub_key not in self.config[key]:
                        self.config[key][sub_key] = sub_value
                        
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logging.info(f"配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            logging.error(f"保存配置文件出错: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 "notification.email.enabled"
            default: 如果键不存在，返回的默认值
            
        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 要设置的值
        """
        keys = key.split('.')
        config = self.config
        
        # 处理嵌套字典
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最终值
        config[keys[-1]] = value
    
    def add_concert(self, concert_info: Dict[str, Any]) -> None:
        """
        添加演唱会信息
        
        Args:
            concert_info: 演唱会信息字典，必须包含 "id" 键
        """
        if "concerts" not in self.config:
            self.config["concerts"] = []
            
        # 检查是否已存在相同ID的演唱会
        existing_ids = [c.get("id") for c in self.config["concerts"]]
        if concert_info.get("id") in existing_ids:
            # 更新现有演唱会信息
            for i, concert in enumerate(self.config["concerts"]):
                if concert.get("id") == concert_info.get("id"):
                    self.config["concerts"][i] = concert_info
                    break
        else:
            # 添加新演唱会
            self.config["concerts"].append(concert_info)
    
    def remove_concert(self, concert_id: str) -> bool:
        """
        删除指定ID的演唱会信息
        
        Args:
            concert_id: 演唱会ID
            
        Returns:
            是否成功删除
        """
        if "concerts" not in self.config:
            return False
            
        for i, concert in enumerate(self.config["concerts"]):
            if concert.get("id") == concert_id:
                del self.config["concerts"][i]
                return True
                
        return False
    
    def get_all_concerts(self) -> List[Dict[str, Any]]:
        """
        获取所有演唱会信息
        
        Returns:
            演唱会信息列表
        """
        return self.config.get("concerts", [])
    
    def get_concert_by_id(self, concert_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取演唱会信息
        
        Args:
            concert_id: 演唱会ID
            
        Returns:
            演唱会信息字典，如果未找到则返回 None
        """
        for concert in self.get_all_concerts():
            if concert.get("id") == concert_id:
                return concert
        return None