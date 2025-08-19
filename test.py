#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
韩国演唱会抢票系统测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("正在测试模块导入...")
    
    try:
        from python.utils.config_manager import ConfigManager
        print("✓ ConfigManager 导入成功")
    except ImportError as e:
        print(f"✗ ConfigManager 导入失败: {e}")
        return False
    
    try:
        from python.utils.logger import setup_logger
        print("✓ Logger 导入成功")
    except ImportError as e:
        print(f"✗ Logger 导入失败: {e}")
        return False
    
    try:
        from python.core.ticket_bot import TicketBot
        print("✓ TicketBot 导入成功")
    except ImportError as e:
        print(f"✗ TicketBot 导入失败: {e}")
        return False
    
    try:
        from python.ui.main_window import MainWindow
        print("✓ MainWindow 导入成功")
    except ImportError as e:
        print(f"✗ MainWindow 导入失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置管理"""
    print("\n正在测试配置管理...")
    
    try:
        from python.utils.config_manager import ConfigManager
        config = ConfigManager()
        print("✓ 配置管理器创建成功")
        
        # 测试获取配置
        app_name = config.get("app.name", "未知")
        print(f"✓ 应用名称: {app_name}")
        
        # 测试获取演唱会列表
        concerts = config.get_all_concerts()
        print(f"✓ 演唱会数量: {len(concerts)}")
        
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """测试日志系统"""
    print("\n正在测试日志系统...")
    
    try:
        from python.utils.logger import setup_logger
        logger = setup_logger()
        logger.info("测试日志消息")
        print("✓ 日志系统测试成功")
        return True
    except Exception as e:
        print(f"✗ 日志测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """测试依赖包"""
    print("\n正在测试依赖包...")
    
    required_packages = [
        ("selenium", "selenium"),
        ("PyQt5", "PyQt5"), 
        ("requests", "requests"),
        ("opencv-python", "cv2"),
        ("pytesseract", "pytesseract"),
        ("numpy", "numpy"),
        ("PIL", "PIL")
    ]
    
    all_ok = True
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name} 可用")
        except ImportError:
            print(f"✗ {package_name} 不可用")
            all_ok = False
    
    return all_ok

def test_file_structure():
    """测试文件结构"""
    print("\n正在测试文件结构...")
    
    required_files = [
        "config/default_config.json",
        "config/config.json",
        "python/main.py",
        "python/requirements.txt",
        "python/core/ticket_bot.py",
        "python/ui/main_window.py",
        "python/utils/config_manager.py"
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_ok = False
    
    return all_ok

def main():
    """主测试函数"""
    print("=" * 50)
    print("韩国演唱会抢票系统 - 系统测试")
    print("=" * 50)
    
    tests = [
        ("文件结构", test_file_structure),
        ("依赖包", test_dependencies),
        ("模块导入", test_imports),
        ("配置管理", test_config),
        ("日志系统", test_logger)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常运行。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
