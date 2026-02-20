@echo off
chcp 65001 >nul
echo ==========================================
echo  齿轮波纹度分析 Web 应用
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist venv (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt -q

REM 启动应用
echo.
echo ==========================================
echo  正在启动 Web 应用...
echo  请在浏览器中访问：http://localhost:8501
echo ==========================================
echo.

streamlit run app.py

pause
