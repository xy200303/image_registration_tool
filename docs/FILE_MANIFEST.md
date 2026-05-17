# 项目结构清单

## 根目录

```text
.
├── src/                          # 应用源码
├── docs/                         # 使用与维护文档
├── scripts/                      # Windows 辅助脚本
├── packaging/                    # 打包配置
├── image_registration_tool.py    # 源码启动入口
├── pyproject.toml                # Python 项目元数据
├── requirements.txt              # 依赖锁定
└── README.md                     # 项目说明
```

## 源码目录

```text
src/image_registration_tool/
├── __init__.py
├── __main__.py
├── cli.py
├── gui.py
└── tools/
    ├── __init__.py
    ├── align.py
    ├── manual_registration.py
    └── split_data.py
```

## 文档目录

```text
docs/
├── BUILD_README.md
└── FILE_MANIFEST.md
```

## 脚本目录

```text
scripts/
├── build.bat
└── clean.bat
```

## 目录职责

- `src/`：正式应用代码，只放可维护的 Python 源码
- `docs/`：文档沉淀，避免说明文件散落在根目录
- `scripts/`：批处理脚本和辅助命令
- `packaging/`：构建和分发相关配置
- 根目录仅保留一个源码启动入口，避免重复脚本散落
