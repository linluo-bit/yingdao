@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo ================================
echo 启动 RPA桌面自动化软件
echo ================================

:: 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在
    echo 请先运行 install.bat 进行安装
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

:: 设置编码环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: 检查main.py
if not exist "main.py" (
    echo ❌ 未找到主程序文件 main.py
    pause
    exit /b 1
)

:: 启动程序
echo 🚀 启动RPA软件...
echo.
python main.py

:: 程序退出后显示信息
echo.
echo ================================
echo 程序已退出
echo ================================
pause 