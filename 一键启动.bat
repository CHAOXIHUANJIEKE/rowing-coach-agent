@echo off
chcp 65001 >nul
echo ============================================
echo   赛艇智能教练 Agent - 一键启动
echo ============================================
echo.
echo 正在启动Web界面...
echo.

cd /d "%~dp0"

REM 尝试找Python
set PYTHON_CMD=

REM 优先用py launcher
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    goto :found
)

REM 尝试python
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    goto :found
)

REM 尝试常见路径
if exist "D:\pycharm\python.exe" (
    set PYTHON_CMD=D:\pycharm\python.exe
    goto :found
)

if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto :found
)

if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :found
)

echo [错误] 未找到Python，请先安装Python 3.8+
echo 下载地址: https://www.python.org/downloads/
echo 安装后请勾选 "Add Python to PATH"
pause
exit /b 1

:found
echo 找到Python: %PYTHON_CMD%
echo 启动后请打开浏览器访问: http://localhost:8000
echo.
echo 按 Ctrl+C 可停止服务
echo.

%PYTHON_CMD% web_app.py

pause