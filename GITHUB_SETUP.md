# GitHub 仓库信息

## 仓库地址

**GitHub**: https://github.com/xy200303/image_registration_tool.git

## 快速开始

### 首次推送

#### 方法一：使用自动脚本（推荐）
```bash
# 双击运行
git_init.bat
```

#### 方法二：手动操作
```bash
# 1. 初始化 Git 仓库
git init

# 2. 添加远程仓库
git remote add origin https://github.com/xy200303/image_registration_tool.git

# 3. 添加所有文件
git add .gitignore
git add *.py
git add *.txt
git add *.md
git add *.spec
git add *.bat

# 4. 提交
git commit -m "Initial commit: Image Registration Tool"

# 5. 推送到 GitHub
git push -u origin master
```

### 后续更新

#### 方法一：使用自动脚本
```bash
# 双击运行
git_commit.bat
```

#### 方法二：手动操作
```bash
# 1. 添加修改的文件
git add image_registration_tool.py

# 2. 提交
git commit -m "Update: 添加新功能"

# 3. 推送
git push
```

## 常用命令

### 查看状态
```bash
git status
```

### 查看修改
```bash
git diff
```

### 查看提交历史
```bash
git log
```

### 拉取更新
```bash
git pull
```

### 推送更新
```bash
git push
```

## 分支管理

### 查看分支
```bash
git branch
```

### 创建新分支
```bash
git branch feature-name
git checkout feature-name
```

### 合并分支
```bash
git checkout master
git merge feature-name
```

## 常见问题

### 推送失败：认证错误
**错误信息**:
```
remote: Permission to xy200303/image_registration_tool.git denied to user
```

**解决方法**:
1. 配置 Git 用户信息：
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```

2. 使用 GitHub Personal Access Token：
   - 访问 https://github.com/settings/tokens
   - 生成新的 Personal Access Token
   - 使用 Token 作为密码

### 推送失败：仓库不存在
**错误信息**:
```
remote: Repository not found
```

**解决方法**:
1. 访问 https://github.com/xy200303/image_registration_tool
2. 如果仓库不存在，点击 "New repository" 创建
3. 仓库名称必须是：image_registration_tool

### 推送失败：分支名称不匹配
**错误信息**:
```
error: src refspec master does not match any
```

**解决方法**:
1. 查看当前分支名称：
   ```bash
   git branch
   ```

2. 如果分支名是 main，使用：
   ```bash
   git push -u origin main
   ```

3. 如果分支名是 master，使用：
   ```bash
   git push -u origin master
   ```

## 工作流程

### 开发新功能
```bash
# 1. 拉取最新代码
git pull

# 2. 创建新分支
git branch feature-new-function
git checkout feature-new-function

# 3. 开发并提交
git add .
git commit -m "Add: 新功能"

# 4. 推送到远程
git push -u origin feature-new-function

# 5. 在 GitHub 上创建 Pull Request
```

### 修复 Bug
```bash
# 1. 拉取最新代码
git pull

# 2. 创建修复分支
git branch fix-bug-name
git checkout fix-bug-name

# 3. 修复并提交
git add .
git commit -m "Fix: 修复某个问题"

# 4. 推送到远程
git push -u origin fix-bug-name

# 5. 在 GitHub 上创建 Pull Request
```

## 提交信息规范

### 格式
```
<类型>: <简短描述>

<详细描述（可选）>
```

### 类型
- `Add`: 添加新功能
- `Fix`: 修复 Bug
- `Update`: 更新现有功能
- `Refactor`: 重构代码
- `Doc`: 文档更新
- `Test`: 添加测试
- `Chore`: 构建/工具链相关

### 示例
```
Add: 添加键盘控制功能

- 支持方向键移动
- 支持长按连续移动
- 支持多键同时按下
```

```
Fix: 修复信号参数不匹配问题

修复 parameters_changed 信号的参数数量不匹配导致的程序崩溃
```

## 相关文档

- `FILE_MANIFEST.md` - 完整文件清单
- `GIT_GUIDE.md` - Git 快速指南
- `GIT_COMMIT_GUIDE.md` - 提交指南
- `README.md` - 项目说明

## 脚本说明

- `git_init.bat` - 初始化仓库并首次推送
- `git_commit.bat` - 提交更新
- `build.bat` - 打包为 exe
- `clean.bat` - 清理构建文件
