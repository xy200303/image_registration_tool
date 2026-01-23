@echo off
chcp 65001 >nul
echo ========================================
echo Git 初始化和推送脚本
echo ========================================
echo.

echo [1/6] 初始化 Git 仓库...
if not exist .git (
    git init
    echo [OK] Git 仓库已初始化
) else (
    echo [SKIP] Git 仓库已存在
)

echo.
echo [2/6] 添加远程仓库...
git remote -v | findstr "xy200303" >nul
if %ERRORLEVEL% NEQ 0 (
    git remote add origin https://github.com/xy200303/image_registration_tool.git
    echo [OK] 远程仓库已添加
) else (
    echo [SKIP] 远程仓库已存在
)

echo.
echo [3/6] 添加所有源代码和配置文件...
git add .gitignore
git add *.py
git add *.txt
git add *.md
git add *.spec
git add *.bat

echo.
echo [4/6] 查看将要提交的文件...
git status

echo.
echo [5/6] 提交到本地仓库...
set /p commit_msg="请输入提交信息: "
if "%commit_msg%"=="" (
    set commit_msg=Initial commit: Image Registration Tool
)

git commit -m "%commit_msg%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo 提交失败！
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo [6/6] 推送到 GitHub...
echo.
echo 正在推送到: https://github.com/xy200303/image_registration_tool.git
echo.
git push -u origin master

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo 推送失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 仓库不存在，请先在 GitHub 上创建仓库
    echo 2. 认证失败，请配置 Git 凭证
    echo 3. 网络连接问题
    echo.
    echo 解决方法：
    echo 1. 访问 https://github.com/xy200303/image_registration_tool 创建仓库
    echo 2. 配置 Git: git config --global user.name "Your Name"
    echo 3. 配置 Git: git config --global user.email "your@email.com"
    echo.
) else (
    echo.
    echo ========================================
    echo 推送成功！
    echo ========================================
    echo.
    echo 仓库地址: https://github.com/xy200303/image_registration_tool.git
    echo.
)

pause
