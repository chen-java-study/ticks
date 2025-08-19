"""
图标资源模块
"""

import os
from pathlib import Path

# 图标目录路径
ICONS_DIR = Path(__file__).parent

def get_icon_path(icon_name: str) -> str:
    """
    获取图标文件路径
    
    Args:
        icon_name: 图标文件名
        
    Returns:
        图标文件的完整路径
    """
    icon_path = ICONS_DIR / f"{icon_name}.png"
    if icon_path.exists():
        return str(icon_path)
    return ""

# 预定义的图标名称
ICONS = {
    "app": "app_icon",
    "play": "play",
    "pause": "pause", 
    "stop": "stop",
    "settings": "settings",
    "add": "add",
    "remove": "remove",
    "edit": "edit",
    "refresh": "refresh",
    "ticket": "ticket",
    "concert": "concert",
    "user": "user",
    "lock": "lock",
    "unlock": "unlock"
}
