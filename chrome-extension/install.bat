@echo off
echo ========================================
echo    RPA元素捕获器 Chrome插件安装脚本
echo ========================================
echo.

REM 检查Chrome是否安装
echo 正在检查Chrome浏览器...
reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Chrome浏览器，请先安装Chrome
    pause
    exit /b 1
)

echo Chrome浏览器已找到
echo.

REM 获取Chrome用户数据目录
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\User Data" /v "Default" 2^>nul') do set CHROME_USER_DATA=%%b
if "%CHROME_USER_DATA%"=="" (
    echo 错误: 无法获取Chrome用户数据目录
    pause
    exit /b 1
)

echo Chrome用户数据目录: %CHROME_USER_DATA%
echo.

REM 创建扩展程序目录
set EXTENSIONS_DIR=%CHROME_USER_DATA%\Default\Extensions\rpa-element-capture
if not exist "%EXTENSIONS_DIR%" (
    mkdir "%EXTENSIONS_DIR%"
    echo 创建扩展程序目录: %EXTENSIONS_DIR%
)

REM 复制插件文件
echo 正在复制插件文件...
xcopy /E /I /Y "%~dp0*" "%EXTENSIONS_DIR%\1.0\"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    插件安装成功！
    echo ========================================
    echo.
    echo 安装步骤:
    echo 1. 打开Chrome浏览器
    echo 2. 在地址栏输入: chrome://extensions/
    echo 3. 开启右上角的"开发者模式"
    echo 4. 点击"加载已解压的扩展程序"
    echo 5. 选择文件夹: %EXTENSIONS_DIR%\1.0\
    echo 6. 插件安装完成！
    echo.
    echo 使用方法:
    echo - 按住Ctrl键进入捕获模式
    echo - 鼠标悬停会高亮显示元素
    echo - 按住Ctrl+鼠标左键点击要捕获的元素
    echo - 点击插件图标查看捕获的元素列表
    echo.
) else (
    echo.
    echo 错误: 插件文件复制失败
    echo 请检查文件权限或手动复制文件
    echo.
)

pause 