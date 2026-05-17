from __future__ import annotations

import json
import random
import shutil
from pathlib import Path


def split_data(
    images_dir: Path | str = Path("images"),
    infrared_dir: Path | str = Path("imagesIR"),
    labels_dir: Path | str = Path("labels"),
    output_dir: Path | str = Path("outputs"),
    ratios: tuple[float, float, float] = (0.7, 0.2, 0.1),
    seed: int = 42,
) -> dict[str, int]:
    images_dir = Path(images_dir)
    infrared_dir = Path(infrared_dir)
    labels_dir = Path(labels_dir)
    output_dir = Path(output_dir)

    src_dirs = {
        "images": images_dir,
        "imagesIR": infrared_dir,
        "labels": labels_dir,
    }
    file_types = {
        "images": [".jpg", ".png", ".jpeg"],
        "imagesIR": [".jpg", ".png", ".jpeg"],
        "labels": [".txt", ".json"],
    }

    for name, directory in src_dirs.items():
        if not directory.exists():
            raise FileNotFoundError(f"{name} 目录不存在: {directory}")

    random.seed(seed)

    image_stems = [
        file_path.stem
        for file_path in images_dir.glob("*")
        if file_path.suffix.lower() in file_types["images"]
    ]
    image_stems = [
        stem
        for stem in image_stems
        if any((infrared_dir / f"{stem}{ext}").exists() for ext in file_types["imagesIR"])
        and any((labels_dir / f"{stem}{ext}").exists() for ext in file_types["labels"])
    ]

    random.shuffle(image_stems)
    total_count = len(image_stems)
    train_count = int(total_count * ratios[0])
    val_count = int(total_count * ratios[1])

    splits = {
        "train": image_stems[:train_count],
        "val": image_stems[train_count : train_count + val_count],
        "test": image_stems[train_count + val_count :],
    }

    print(
        f"总数: {total_count}, "
        f"训练: {len(splits['train'])}, "
        f"验证: {len(splits['val'])}, "
        f"测试: {len(splits['test'])}"
    )

    for data_type in src_dirs:
        for split_name in splits:
            (output_dir / data_type / split_name).mkdir(parents=True, exist_ok=True)

    for split_name, stems in splits.items():
        for stem in stems:
            for data_type, src_dir in src_dirs.items():
                for ext in file_types[data_type]:
                    src_file = src_dir / f"{stem}{ext}"
                    if src_file.exists():
                        shutil.copy2(src_file, output_dir / data_type / split_name / src_file.name)
                        break

    info_dir = output_dir / "info"
    info_dir.mkdir(exist_ok=True)
    split_info = {"counts": {name: len(items) for name, items in splits.items()}}
    with (info_dir / "split.json").open("w", encoding="utf-8") as file:
        json.dump(split_info, file, indent=2, ensure_ascii=False)

    print(f"完成！输出到: {output_dir}")
    return split_info["counts"]
