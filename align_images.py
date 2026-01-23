import os
import cv2
import numpy as np

R_PATH = "./imagesIR_registered"
VIS_PATH = "./images"
OUTPUT_PATH = "./images_aligned"

def align_images():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    file_list = sorted(os.listdir(R_PATH))
    
    print("开始对齐可见光图像...")
    print("=" * 50)
    
    success_count = 0
    skip_count = 0
    
    for i, file_name in enumerate(file_list):
        ir_file = os.path.join(R_PATH, file_name)
        vis_file = os.path.join(VIS_PATH, file_name)
        output_file = os.path.join(OUTPUT_PATH, file_name)
        
        if not os.path.exists(vis_file):
            print(f"[{i+1}/{len(file_list)}] 可见光图像不存在: {file_name}, 跳过")
            skip_count += 1
            continue
        
        ir_img = cv2.imread(ir_file)
        vis_img = cv2.imread(vis_file)
        
        if ir_img is None:
            print(f"[{i+1}/{len(file_list)}] 无法读取红外图像: {file_name}, 跳过")
            skip_count += 1
            continue
        
        if vis_img is None:
            print(f"[{i+1}/{len(file_list)}] 无法读取可见光图像: {file_name}, 跳过")
            skip_count += 1
            continue
        
        h, w = ir_img.shape[:2]
        
        if vis_img.shape[:2] == (h, w):
            aligned_img = vis_img.copy()
        else:
            aligned_img = cv2.resize(vis_img, (w, h), interpolation=cv2.INTER_LINEAR)
        
        cv2.imwrite(output_file, aligned_img)
        success_count += 1
        
        print(f"[{i+1}/{len(file_list)}] 已处理: {file_name} -> 尺寸: {w}x{h}")
    
    print("=" * 50)
    print(f"对齐完成!")
    print(f"成功处理: {success_count} 张")
    print(f"跳过: {skip_count} 张")
    print(f"输出目录: {OUTPUT_PATH}")

if __name__ == "__main__":
    align_images()
