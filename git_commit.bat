@echo off
chcp 65001 >nul
echo ========================================
echo Git 提交脚本
echo ========================================
echo.

echo [1/4] 检查 Git 状态...
git status

echo.
echo [2/4] 添加所有源代码和配置文件...
git add .gitignore
git add *.py
git add *.txt
git add *.md
git add *.spec
git add *.bat

echo.
echo [3/4] 查看将要提交的文件...
git status

echo.
echo [4/4] 提交到 Git...
set /p commit_msg="请输入提交信息: "
if "%commit_msg%"=="" (
    set commit_msg=Update files
)

git commit -m "%commit_msg%"

echo.
echo ========================================
echo 提交完成！
echo ========================================
echo.
echo 如需推送到远程仓库，请运行:
echo git push
echo.
pause
