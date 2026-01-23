import os
import shutil
import random
import json
from pathlib import Path

def split_data():
    """最简洁的版本"""
    # 配置
    src = {
        'images': Path('./images'),
        'imagesIR': Path('./imagesIR'),
        'labels': Path('./labels')
    }
    output = Path('./outputs')
    ratios = (0.7, 0.2, 0.1)  # train, val, test
    seed = 42

    # 文件类型映射
    file_types = {
        'images': ['.jpg', '.png', '.jpeg'],
        'imagesIR': ['.jpg', '.png', '.jpeg'],
        'labels': ['.txt', '.json']
    }

    random.seed(seed)

    # 获取所有图片名
    pics = [f.stem for f in src['images'].glob('*') if f.suffix.lower() in file_types['images']]
    pics = [p for p in pics if
            any((src['imagesIR'] / f"{p}{ext}").exists() for ext in file_types['imagesIR']) and
            any((src['labels'] / f"{p}{ext}").exists() for ext in file_types['labels'])]

    random.shuffle(pics)
    n = len(pics)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])

    splits = {
        'train': pics[:n_train],
        'val': pics[n_train:n_train+n_val],
        'test': pics[n_train+n_val:]
    }

    print(f"总数: {n}, 训练: {len(splits['train'])}, 验证: {len(splits['val'])}, 测试: {len(splits['test'])}")

    # 创建目录
    for dtype in ['images', 'imagesIR', 'labels']:
        for split in ['train', 'val', 'test']:
            (output / dtype / split).mkdir(parents=True, exist_ok=True)

    # 复制文件
    for split_name, files in splits.items():
        for stem in files:
            for dtype, src_dir in src.items():
                # 只复制指定类型的文件
                for ext in file_types[dtype]:
                    src_file = src_dir / f"{stem}{ext}"
                    if src_file.exists():
                        dst = output / dtype / split_name / src_file.name
                        shutil.copy2(src_file, dst)
                        break  # 只复制第一个匹配的文件

    # 保存信息
    info = {'counts': {k: len(v) for k, v in splits.items()}}
    (output / 'info').mkdir(exist_ok=True)
    with open(output / 'info' / 'split.json', 'w') as f:
        json.dump(info, f, indent=2)

    print(f"完成！输出到: {output}")

if __name__ == "__main__":
    split_data()
