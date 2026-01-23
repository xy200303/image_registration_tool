# Git 提交文件清单

## 项目结构

```
JZ_data/
├── .gitignore                    # Git 忽略文件配置
├── .venv/                      # 虚拟环境（已忽略）
├── images/                      # 可见光图像数据（已忽略）
├── imagesIR/                    # 红外图像数据（已忽略）
├── test/                       # 测试图像数据（已忽略）
├── results/                     # 配准参数结果（已忽略）
├── build/                      # PyInstaller 构建目录（已忽略）
├── dist/                       # PyInstaller 输出目录（已忽略）
│
├── Python 源代码文件
│   ├── image_registration_tool.py  # 主程序：图像配准工具（GUI）
│   ├── app.py                   # 旧版程序
│   ├── align_images.py           # 图像对齐脚本
│   ├── manual_registration.py    # 手动配准脚本
│   └── split_data.py            # 数据分割脚本
│
├── 配置文件
│   ├── requirements.txt           # Python 依赖包列表
│   └── image_registration_tool.spec  # PyInstaller 打包配置
│
├── 构建脚本
│   ├── build.bat                # Windows 打包脚本
│   └── clean.bat               # 清理构建文件脚本
│
└── 文档
    ├── README.md                # 项目说明文档
    └── BUILD_README.md         # 打包说明文档
```

## 应提交到 Git 的文件

### 核心程序文件
- ✅ `image_registration_tool.py` - 主程序（图像配准工具 GUI）
- ✅ `app.py` - 辅助程序
- ✅ `align_images.py` - 图像对齐工具
- ✅ `manual_registration.py` - 手动配准工具
- ✅ `split_data.py` - 数据分割工具

### 配置文件
- ✅ `requirements.txt` - Python 依赖包
- ✅ `image_registration_tool.spec` - PyInstaller 配置

### 构建脚本
- ✅ `build.bat` - 自动打包脚本
- ✅ `clean.bat` - 清理脚本

### 文档文件
- ✅ `README.md` - 项目说明
- ✅ `BUILD_README.md` - 打包说明
- ✅ `.gitignore` - Git 忽略配置

## 不应提交到 Git 的文件（已在 .gitignore 中配置）

### 虚拟环境
- ❌ `.venv/` - Python 虚拟环境

### 构建产物
- ❌ `build/` - PyInstaller 构建临时文件
- ❌ `dist/` - PyInstaller 输出的 exe 文件
- ❌ `*.log` - 构建日志

### 图像数据
- ❌ `images/` - 可见光图像数据
- ❌ `imagesIR/` - 红外图像数据
- ❌ `test/` - 测试图像数据
- ❌ `results/` - 配准参数结果
- ❌ `*.png`, `*.jpg`, `*.jpeg`, `*.bmp` - 所有图像文件

### IDE 配置
- ❌ `.idea/` - PyCharm 配置
- ❌ `.vscode/` - VS Code 配置
- ❌ `*.swp`, `*.swo` - Vim 临时文件

### 操作系统文件
- ❌ `Thumbs.db` - Windows 缩略图
- ❌ `Desktop.ini` - Windows 配置
- ❌ `.DS_Store` - macOS 系统文件

## Git 提交建议

### 首次提交
```bash
git init
git add .gitignore
git add image_registration_tool.py
git add app.py
git add align_images.py
git add manual_registration.py
git add split_data.py
git add requirements.txt
git add image_registration_tool.spec
git add build.bat
git add clean.bat
git add README.md
git add BUILD_README.md
git commit -m "Initial commit: Image Registration Tool"
```

### 后续更新
```bash
# 添加修改的文件
git add image_registration_tool.py
git add README.md

# 提交
git commit -m "Update: 添加新功能"
```

### 查看状态
```bash
git status
```

### 查看将要提交的文件
```bash
git diff --cached
```

## 文件说明

### image_registration_tool.py
- **功能**: 图像配准工具主程序
- **特性**:
  - PyQt6 GUI 界面
  - 支持红外和可见光图像配准
  - 全局/手动两种模式
  - 键盘和鼠标控制
  - 批量导出功能
  - 参数保存和加载

### requirements.txt
- **内容**: 项目依赖的 Python 包
- **主要依赖**:
  - PyQt6
  - opencv-python
  - numpy

### build.bat
- **功能**: 自动打包脚本
- **用途**: 将 Python 程序打包为 Windows exe 文件

### clean.bat
- **功能**: 清理构建文件
- **用途**: 删除 build/ 和 dist/ 目录

## 注意事项

1. **不要提交大文件**: 图像数据文件很大，不应提交到 git
2. **不要提交虚拟环境**: .venv/ 目录应在本地创建
3. **不要提交构建产物**: build/ 和 dist/ 目录是临时文件
4. **保持 .gitignore 更新**: 添加新的临时文件类型时更新 .gitignore

## 数据处理流程

1. 克隆仓库后，在本地创建虚拟环境：
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. 准备图像数据：
   - 创建 `images/` 目录存放可见光图像
   - 创建 `imagesIR/` 目录存放红外图像
   - （可选）创建 `test/` 目录存放测试图像

3. 运行程序：
   ```bash
   python image_registration_tool.py
   ```

4. 配准结果会自动保存到 `results/` 目录

## 打包发布

如需打包为 exe 文件：
```bash
# 运行打包脚本
build.bat

# 或手动打包
pyinstaller image_registration_tool.spec
```

打包后的 exe 文件位于 `dist/ImageRegistrationTool.exe`
