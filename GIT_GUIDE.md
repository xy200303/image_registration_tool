# Git 提交快速指南

## 快速开始

### 首次提交
```bash
git init
git add .gitignore
git add *.py
git add *.txt
git add *.md
git add *.spec
git add *.bat
git commit -m "Initial commit: Image Registration Tool"
```

### 后续更新
```bash
# 方法一：使用自动脚本（推荐）
git_commit.bat

# 方法二：手动提交
git add image_registration_tool.py
git commit -m "Update: 添加新功能"
```

## 应提交的文件

### ✅ 必须提交
- `image_registration_tool.py` - 主程序
- `requirements.txt` - 依赖包
- `image_registration_tool.spec` - 打包配置
- `build.bat` - 打包脚本
- `clean.bat` - 清理脚本
- `README.md` - 项目说明
- `BUILD_README.md` - 打包说明
- `.gitignore` - Git 配置

### ❌ 不应提交（已在 .gitignore 中）
- `.venv/` - 虚拟环境
- `build/` - 构建临时文件
- `dist/` - 打包输出
- `images/` - 图像数据
- `imagesIR/` - 图像数据
- `test/` - 测试数据
- `results/` - 配准结果
- `*.png`, `*.jpg` - 图像文件
- `.idea/` - IDE 配置

## 常用命令

```bash
# 查看状态
git status

# 查看修改
git diff

# 添加文件
git add <filename>

# 提交
git commit -m "提交信息"

# 推送到远程
git push

# 拉取更新
git pull
```

## 详细说明

请查看 `FILE_MANIFEST.md` 获取完整的文件清单和详细说明。
