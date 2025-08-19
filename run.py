#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
韩国演唱会抢票系统启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 导入主程序
from python.main import main

if __name__ == "__main__":
    main()
