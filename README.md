# 图像配准工具

一个更正式整理后的 Python 项目，用于红外图像与可见光图像的手动配准、批量导出和数据集辅助处理。

## 项目特性

- PyQt6 图形界面，支持人工调节红外/可见光图像配准
- 支持当前图像一键自动优化 `dx / dy / scale_x / scale_y`
- 支持整目录批量自动优化并保存参数
- 内置统一 CLI，可运行配准、尺寸对齐和数据集拆分
- 使用 `src/` 包结构，便于维护、安装和后续扩展

## 项目结构

```text
.
├── src/
│   └── image_registration_tool/
│       ├── gui.py                  # 主 GUI
│       ├── cli.py                  # 统一命令行入口
│       └── tools/
│           ├── align.py            # 可见光图像尺寸对齐
│           ├── manual_registration.py
│           └── split_data.py
├── scripts/                        # Windows 辅助脚本
├── docs/                           # 项目文档
├── packaging/                      # 打包配置
├── image_registration_tool.py      # 源码启动入口
├── pyproject.toml                  # 项目元数据
└── requirements.txt                # 依赖锁定
```

## 安装

### 方式一：直接安装依赖

```bash
pip install -r requirements.txt
```

### 方式二：按项目方式安装

```bash
pip install -e .
```

## 运行方式

### 启动主 GUI

兼容方式：

```bash
python image_registration_tool.py
```

运行其他子命令：

```bash
python image_registration_tool.py align
python image_registration_tool.py manual
python image_registration_tool.py split-data
```

安装后推荐方式：

```bash
image-registration-tool gui
image-registration-tool align
image-registration-tool manual
image-registration-tool split-data
```

### GUI 自动优化

在主界面中点击 `一键自动优化` 按钮后，程序会：

- 以当前参数作为初始值
- 使用 ECC 生成初始估计
- 基于 SciPy 对 `dx / dy / scale_x / scale_y` 继续精修
- 自动刷新预览并将结果写入 `results/` 参数文件

点击 `批量自动优化` 按钮后，程序会按目录逐张处理，并优先复用已有参数或上一张优化结果作为下一张的初始值。

## 默认目录约定

默认使用当前工作目录下的这些目录：

- `images/`：可见光图像
- `imagesIR/`：红外图像
- `results/`：GUI 保存的配准参数
- `imagesIR_registered/`：手动配准后的红外图像
- `images_aligned/`：按红外尺寸对齐后的可见光图像
- `outputs/`：数据集拆分输出目录

## 路径兼容

- Windows 下直接使用 `cv2.imread` / `cv2.imwrite` 处理中文路径时，常会出现读取或导出失败
- 本项目已经统一改为 `cv2.imdecode` / `cv2.imencode` 方案，兼容中文路径和当前这类中文项目目录
- 如果你后续新增图像读写代码，建议继续复用项目内的 [src/image_registration_tool/io.py](</c:/Users/34834/Desktop/projectM/python/图像配准工具/src/image_registration_tool/io.py:1>)

## 开发与打包

- 打包说明见 [docs/BUILD_README.md](docs/BUILD_README.md)
- 项目结构清单见 [docs/FILE_MANIFEST.md](docs/FILE_MANIFEST.md)

## 注意事项

- 红外图像和可见光图像默认按同名文件匹配
- 当前 GUI 仍以手动配准为核心，未引入自动配准算法
- 如果直接通过源码运行，建议在项目根目录执行命令，以保持默认路径一致
