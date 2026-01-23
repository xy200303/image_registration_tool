# Image Registration Tool - 打包说明

## 文件说明

- `image_registration_tool.py` - 主程序文件
- `image_registration_tool.spec` - PyInstaller 配置文件
- `build.bat` - Windows 打包脚本

## 打包步骤

### 方法一：使用批处理脚本（推荐）

1. 双击运行 `build.bat`
2. 等待打包完成
3. 在 `dist` 目录下找到 `ImageRegistrationTool.exe`

### 方法二：手动打包

1. 激活虚拟环境：
   ```bash
   .venv\Scripts\activate
   ```

2. 安装 PyInstaller（如果尚未安装）：
   ```bash
   pip install pyinstaller
   ```

3. 使用 spec 文件打包：
   ```bash
   pyinstaller image_registration_tool.spec
   ```

4. 打包完成后，在 `dist` 目录下找到 `ImageRegistrationTool.exe`

## 输出文件

打包成功后，会在项目目录下生成以下文件：

- `build/` - 临时构建目录（可删除）
- `dist/ImageRegistrationTool.exe` - 最终的可执行文件

## 运行程序

直接双击 `dist/ImageRegistrationTool.exe` 即可运行程序。

## 注意事项

1. **首次运行**：首次运行时可能需要防火墙或杀毒软件的允许
2. **依赖项**：程序已包含所有必要的依赖库，无需额外安装 Python
3. **文件大小**：打包后的 exe 文件较大（约 100-200 MB），这是正常的
4. **results 目录**：程序会在同目录下自动创建 `results` 文件夹用于保存配准参数

## 清理构建文件

如果需要清理构建文件，可以删除以下目录：
- `build/` - 临时构建目录
- `dist/` - 输出目录（如果要重新打包）

## 自定义打包

如果需要修改打包配置，编辑 `image_registration_tool.spec` 文件：

- `name='ImageRegistrationTool'` - 修改输出文件名
- `console=False` - 设置为 True 显示控制台窗口
- `icon=None` - 添加图标文件路径，例如 `icon='app.ico'`

## 添加图标

1. 准备一个 `.ico` 格式的图标文件（例如 `app.ico`）
2. 将图标文件放在项目根目录
3. 修改 spec 文件中的 `icon` 参数：
   ```python
   icon='app.ico'
   ```
4. 重新运行打包脚本
