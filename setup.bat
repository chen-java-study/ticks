@echo off
chcp 65001 >nul
echo 正在设置韩国演唱会抢票系统环境...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo Python版本检查通过
echo.

REM 创建虚拟环境
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

echo.

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级pip
echo 正在升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 正在安装依赖包...
pip install -r python\requirements.txt

if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 环境设置完成！
echo 现在可以运行 start.bat 启动程序
echo.
pause
