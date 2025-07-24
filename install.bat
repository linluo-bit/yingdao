@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo ================================
echo RPA桌面自动化软件 - 一键安装脚本
echo ================================
echo.

:: 检查Python版本
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请先安装Python 3.10或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 显示Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%

:: 检查pip
echo.
echo [2/6] 检查pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: pip未安装
    pause
    exit /b 1
)
echo ✅ pip可用

:: 升级pip
echo.
echo [3/6] 升级pip到最新版本...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  pip升级失败，继续安装...
)

:: 创建虚拟环境
echo.
echo [4/6] 创建虚拟环境...
if exist "venv" (
    echo ⚠️  虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建完成
)

:: 激活虚拟环境
echo.
echo [5/6] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境已激活

:: 设置编码环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: 安装依赖
echo.
echo [6/6] 安装项目依赖...
echo 这可能需要几分钟时间，请耐心等待...

:: 分别安装关键包，避免版本冲突
python -m pip install --upgrade pip setuptools wheel
python -m pip install PyQt6==6.6.0
python -m pip install selenium requests beautifulsoup4
python -m pip install pyautogui pynput
python -m pip install opencv-python Pillow numpy
python -m pip install SQLAlchemy pydantic structlog

:: 安装剩余包
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ⚠️  部分依赖安装可能失败，但核心功能应该可用
    echo 如需完整功能，请手动安装失败的包：
    echo python -m pip install -force-reinstall -r requirements.txt
) else (
    echo ✅ 所有依赖安装完成
)

echo.
echo ================================
echo 🎉 安装完成！
echo ================================
echo.
echo 使用方法:
echo 1. 激活虚拟环境: venv\Scripts\activate.bat
echo 2. 运行程序: python main.py
echo.
echo 或者直接运行: run.bat
echo.
echo 如有问题，请查看README.md文档
echo ================================

pause 