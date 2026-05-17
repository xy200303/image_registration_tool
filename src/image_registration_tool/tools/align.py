from __future__ import annotations

from pathlib import Path

import cv2

from ..io import read_image, write_image


def align_images(
    registered_dir: Path | str = Path("imagesIR_registered"),
    visible_dir: Path | str = Path("images"),
    output_dir: Path | str = Path("images_aligned"),
) -> dict[str, int | str]:
    registered_dir = Path(registered_dir)
    visible_dir = Path(visible_dir)
    output_dir = Path(output_dir)

    if not registered_dir.exists():
        raise FileNotFoundError(f"红外配准目录不存在: {registered_dir}")
    if not visible_dir.exists():
        raise FileNotFoundError(f"可见光目录不存在: {visible_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    file_list = sorted(path.name for path in registered_dir.iterdir() if path.is_file())

    print("开始对齐可见光图像...")
    print("=" * 50)

    success_count = 0
    skip_count = 0

    for index, file_name in enumerate(file_list, start=1):
        ir_file = registered_dir / file_name
        vis_file = visible_dir / file_name
        output_file = output_dir / file_name

        if not vis_file.exists():
            print(f"[{index}/{len(file_list)}] 可见光图像不存在: {file_name}, 跳过")
            skip_count += 1
            continue

        ir_img = read_image(ir_file)
        vis_img = read_image(vis_file)

        if ir_img is None:
            print(f"[{index}/{len(file_list)}] 无法读取红外图像: {file_name}, 跳过")
            skip_count += 1
            continue

        if vis_img is None:
            print(f"[{index}/{len(file_list)}] 无法读取可见光图像: {file_name}, 跳过")
            skip_count += 1
            continue

        height, width = ir_img.shape[:2]
        aligned_img = vis_img if vis_img.shape[:2] == (height, width) else cv2.resize(
            vis_img,
            (width, height),
            interpolation=cv2.INTER_LINEAR,
        )

        if write_image(output_file, aligned_img):
            success_count += 1
            print(f"[{index}/{len(file_list)}] 已处理: {file_name} -> 尺寸: {width}x{height}")
        else:
            skip_count += 1
            print(f"[{index}/{len(file_list)}] 输出失败: {file_name}, 跳过")

    print("=" * 50)
    print("对齐完成!")
    print(f"成功处理: {success_count} 张")
    print(f"跳过: {skip_count} 张")
    print(f"输出目录: {output_dir}")

    return {
        "success_count": success_count,
        "skip_count": skip_count,
        "output_dir": str(output_dir),
    }
