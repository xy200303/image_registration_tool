# Git 提交文件清单

## 创建的文件

### 1. `.gitignore` - Git 忽略配置
忽略以下文件和目录：
- 虚拟环境（.venv/）
- 构建产物（build/, dist/）
- 图像数据（images/, imagesIR/, test/）
- 配准结果（results/）
- IDE 配置（.idea/, .vscode/）
- 系统文件（Thumbs.db, .DS_Store）

### 2. `FILE_MANIFEST.md` - 完整文件清单
包含：
- 项目结构说明
- 应提交/不应提交的文件列表
- Git 提交建议
- 文件详细说明
- 数据处理流程

### 3. `GIT_GUIDE.md` - Git 快速指南
包含：
- 快速开始指南
- 常用 Git 命令
- 提交文件列表

### 4. `git_commit.bat` - 自动提交脚本
功能：
- 自动添加所有源代码和配置文件
- 显示 Git 状态
- 提示输入提交信息
- 执行提交

## 使用方法

### 方法一：使用自动脚本（推荐）
```bash
# 双击运行
git_commit.bat
```

### 方法二：手动提交
```bash
# 首次提交
git init
git add .gitignore
git add *.py
git add *.txt
git add *.md
git add *.spec
git add *.bat
git commit -m "Initial commit"

# 后续更新
git add image_registration_tool.py
git commit -m "Update: 添加新功能"
```

## 应提交的文件清单

### 核心程序
- ✅ image_registration_tool.py
- ✅ app.py
- ✅ align_images.py
- ✅ manual_registration.py
- ✅ split_data.py

### 配置文件
- ✅ requirements.txt
- ✅ image_registration_tool.spec

### 构建脚本
- ✅ build.bat
- ✅ clean.bat
- ✅ git_commit.bat

### 文档文件
- ✅ README.md
- ✅ BUILD_README.md
- ✅ FILE_MANIFEST.md
- ✅ GIT_GUIDE.md
- ✅ .gitignore

## 不应提交的文件（已忽略）

### 虚拟环境
- ❌ .venv/

### 构建产物
- ❌ build/
- ❌ dist/
- ❌ *.log

### 图像数据
- ❌ images/
- ❌ imagesIR/
- ❌ test/
- ❌ results/
- ❌ *.png, *.jpg, *.jpeg, *.bmp

### IDE 配置
- ❌ .idea/
- ❌ .vscode/
- ❌ *.swp, *.swo

### 系统文件
- ❌ Thumbs.db
- ❌ Desktop.ini
- ❌ .DS_Store

## 查看文档

- `FILE_MANIFEST.md` - 完整的文件清单和详细说明
- `GIT_GUIDE.md` - Git 快速指南
- `README.md` - 项目说明
- `BUILD_README.md` - 打包说明

## 注意事项

1. **不要提交大文件**: 图像数据文件很大，不应提交到 git
2. **不要提交虚拟环境**: .venv/ 目录应在本地创建
3. **不要提交构建产物**: build/ 和 dist/ 目录是临时文件
4. **保持 .gitignore 更新**: 添加新的临时文件类型时更新 .gitignore

## 快速命令参考

```bash
# 初始化仓库
git init

# 查看状态
git status

# 添加文件
git add .

# 提交
git commit -m "提交信息"

# 推送
git push

# 拉取
git pull
```

## 准备提交

1. 确认 `.gitignore` 文件已创建
2. 确认所有源代码文件已准备好
3. 运行 `git_commit.bat` 或手动执行 git 命令
4. 查看提交结果
5. 推送到远程仓库（如果需要）

## 文件大小参考

- image_registration_tool.py: ~30 KB
- requirements.txt: ~1 KB
- *.md 文档: ~5-10 KB
- *.bat 脚本: ~1-2 KB

总计：约 50-100 KB（不含图像数据）
