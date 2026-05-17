# 打包说明

## 当前打包方式

项目已整理为 `src/` 包结构，PyInstaller 配置位于：

```text
packaging/image_registration_tool.spec
```

Windows 打包脚本位于：

```text
scripts/build.bat
```

## 打包步骤

### 方式一：直接运行脚本

在项目根目录执行：

```bat
scripts\build.bat
```

### 方式二：手动执行

```bash
.venv\Scripts\activate
pip install pyinstaller
pyinstaller packaging\image_registration_tool.spec --noconfirm
```

## 打包产物

完成后会生成：

```text
build/
dist/ImageRegistrationTool/
```

如果需要单独查看主程序，可在 `dist/ImageRegistrationTool/` 中找到对应可执行文件。

## 说明

- PyInstaller 入口使用根目录下的 `image_registration_tool.py` 源码启动文件
- `pathex` 已包含项目根目录和 `src/` 目录，便于打包后正确导入包
- 由于 GUI 依赖较多，生成体积偏大属于正常现象

## 清理构建产物

在项目根目录执行：

```bat
scripts\clean.bat
```
