@echo off
chcp 65001 >nul
echo 正在运行韩国演唱会抢票系统测试...
echo.

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行测试
python test.py

echo.
pause
