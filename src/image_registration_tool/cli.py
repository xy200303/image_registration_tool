from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-registration-tool",
        description="图像配准工具的统一命令行入口。",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("gui", help="启动主 GUI。")
    align_parser = subparsers.add_parser("align", help="对齐可见光图像尺寸。")
    align_parser.add_argument("--registered-dir", type=Path, default=Path("imagesIR_registered"))
    align_parser.add_argument("--visible-dir", type=Path, default=Path("images"))
    align_parser.add_argument("--output-dir", type=Path, default=Path("images_aligned"))

    manual_parser = subparsers.add_parser("manual", help="运行 OpenCV 版交互式批量配准。")
    manual_parser.add_argument("--ir-dir", type=Path, default=Path("imagesIR"))
    manual_parser.add_argument("--visible-dir", type=Path, default=Path("images"))
    manual_parser.add_argument("--output-dir", type=Path, default=Path("imagesIR_registered"))

    split_parser = subparsers.add_parser("split-data", help="拆分训练/验证/测试集。")
    split_parser.add_argument("--images-dir", type=Path, default=Path("images"))
    split_parser.add_argument("--infrared-dir", type=Path, default=Path("imagesIR"))
    split_parser.add_argument("--labels-dir", type=Path, default=Path("labels"))
    split_parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    split_parser.add_argument("--train-ratio", type=float, default=0.7)
    split_parser.add_argument("--val-ratio", type=float, default=0.2)
    split_parser.add_argument("--test-ratio", type=float, default=0.1)
    split_parser.add_argument("--seed", type=int, default=42)

    return parser


def _handle_gui_import_error(exc: ImportError) -> int:
    message = str(exc)
    print("GUI 启动失败：PyQt6/Qt 运行时未正确加载。", file=sys.stderr)
    print(f"原始错误：{message}", file=sys.stderr)
    print("", file=sys.stderr)
    print("建议执行以下命令修复当前环境：", file=sys.stderr)
    print('python -m pip install --force-reinstall "PyQt6==6.6.1" "PyQt6-Qt6==6.6.1"', file=sys.stderr)
    print("", file=sys.stderr)
    print("如果仍失败，请补装 Microsoft Visual C++ Redistributable。", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "gui"

    if command == "gui":
        try:
            from .gui import main as gui_main
        except ImportError as exc:
            if "QtCore" in str(exc) or "DLL load failed" in str(exc):
                return _handle_gui_import_error(exc)
            raise

        return gui_main()

    if command == "align":
        from .tools.align import align_images

        align_images(
            registered_dir=args.registered_dir,
            visible_dir=args.visible_dir,
            output_dir=args.output_dir,
        )
        return 0

    if command == "manual":
        from .tools.manual_registration import run_batch_registration

        run_batch_registration(
            ir_dir=args.ir_dir,
            visible_dir=args.visible_dir,
            output_dir=args.output_dir,
        )
        return 0

    if command == "split-data":
        from .tools.split_data import split_data

        ratio_sum = args.train_ratio + args.val_ratio + args.test_ratio
        if abs(ratio_sum - 1.0) > 1e-9:
            parser.error("train/val/test 比例之和必须为 1.0")

        split_data(
            images_dir=args.images_dir,
            infrared_dir=args.infrared_dir,
            labels_dir=args.labels_dir,
            output_dir=args.output_dir,
            ratios=(args.train_ratio, args.val_ratio, args.test_ratio),
            seed=args.seed,
        )
        return 0

    parser.error(f"未知命令: {command}")
    return 2
