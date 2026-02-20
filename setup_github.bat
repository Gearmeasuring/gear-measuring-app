@echo off
chcp 65001
cls

echo ==========================================
echo   GitHub 仓库初始化脚本
echo ==========================================
echo.

REM 检查是否安装了 git
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 Git，请先安装 Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM 配置 Git 用户信息（如果还没有配置）
echo 配置 Git 用户信息...
git config --global user.name "Your Name" 2>nul || echo 用户名已配置
git config --global user.email "your.email@example.com" 2>nul || echo 邮箱已配置
echo.

REM 初始化 Git 仓库
echo 初始化 Git 仓库...
git init

REM 添加所有文件
echo 添加文件到仓库...
git add .

REM 提交
echo 提交更改...
git commit -m "Initial commit: 齿轮测量报告系统"

echo.
echo ==========================================
echo   本地仓库已创建！
echo ==========================================
echo.
echo 下一步操作：
echo 1. 在 GitHub 上创建新仓库（不要初始化 README）
echo 2. 运行以下命令关联远程仓库：
echo.
echo    git remote add origin https://github.com/你的用户名/仓库名.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 或者使用 GitHub Desktop 进行可视化操作
echo.
pause
