@echo off
chcp 65001 >nul
echo 正在构建Go语言抢票系统...

REM 检查Go是否安装
go version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Go语言环境，请先安装Go
    pause
    exit /b 1
)

REM 进入Go目录
cd /d "%~dp0"

REM 下载依赖
echo 下载依赖...
go mod tidy

REM 构建程序
echo 构建程序...
go build -o ticket_grabber.exe .

if errorlevel 1 (
    echo 构建失败
    pause
    exit /b 1
)

echo 构建成功！可执行文件: ticket_grabber.exe
echo.
echo 使用方法:
echo ticket_grabber.exe --help
echo ticket_grabber.exe --concert concert_001
echo ticket_grabber.exe --headless --concert concert_001

pause
