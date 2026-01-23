import os
import cv2
import numpy as np

R_PATH = "./imagesIR"
VIS_PATH = "./images"
OUTPUT_PATH = "./imagesIR_registered"

class InteractiveRegistration:
    def __init__(self, ir_img, vis_img, global_dx=0, global_dy=0, global_scale_x=1.0, global_scale_y=1.0):
        self.ir_img = ir_img
        self.vis_img = vis_img
        self.dx = global_dx
        self.dy = global_dy
        self.scale_x = global_scale_x
        self.scale_y = global_scale_y
        self.alpha = 0.5
        self.running = True
        self.use_global = True
        
        h, w = ir_img.shape[:2]
        if vis_img.shape[:2] != (h, w):
            self.vis_img = cv2.resize(vis_img, (w, h))
    
    def update_display(self):
        h, w = self.ir_img.shape[:2]
        center = (w // 2, h // 2)
        
        M_scale = cv2.getRotationMatrix2D(center, 0, 1.0)
        M_scale[0, 0] *= self.scale_x
        M_scale[1, 1] *= self.scale_y
        M_scale[0, 2] += self.dx
        M_scale[1, 2] += self.dy
        
        transformed_ir = cv2.warpAffine(self.ir_img, M_scale, (w, h))
        
        blended = cv2.addWeighted(self.vis_img, self.alpha, transformed_ir, 1 - self.alpha, 0)
        
        display = blended.copy()
        
        mode_text = "Mode: Global" if self.use_global else "Mode: Manual"
        info_text = f"{mode_text} | Offset: dx={self.dx}, dy={self.dy}, ScaleX={self.scale_x:.3f}, ScaleY={self.scale_y:.3f}"
        help_text = "Arrows: Move | W/E: ScaleX | A/D: ScaleY | G: Toggle Mode | +/-: Blend | S: Save | Q: Quit"
        
        cv2.putText(display, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display, help_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow('Registration', display)
    
    def handle_key(self, key):
        if key == 27 or key == ord('q'):
            self.running = False
            return False
        
        elif key == ord('s') or key == ord('S'):
            return True
        
        elif key == ord('g') or key == ord('G'):
            self.use_global = not self.use_global
        
        elif not self.use_global:
            if key == 2424832:
                self.dx -= 1
            elif key == 2555904:
                self.dx += 1
            elif key == 2490368:
                self.dy -= 1
            elif key == 2621440:
                self.dy += 1
            elif key == ord('w') or key == ord('W'):
                self.scale_x = min(2.0, self.scale_x + 0.01)
            elif key == ord('e') or key == ord('E'):
                self.scale_x = max(0.5, self.scale_x - 0.01)
            elif key == ord('d') or key == ord('D'):
                self.scale_y = min(2.0, self.scale_y + 0.01)
            elif key == ord('a') or key == ord('A'):
                self.scale_y = max(0.5, self.scale_y - 0.01)
        
        if key == ord('+') or key == ord('='):
            self.alpha = min(1.0, self.alpha + 0.1)
        elif key == ord('-'):
            self.alpha = max(0.0, self.alpha - 0.1)
        
        return False
    
    def run(self):
        cv2.namedWindow('Registration', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Registration', 800, 600)
        
        while self.running:
            self.update_display()
            key = cv2.waitKeyEx(0) & 0xFFFFFFFF
            save = self.handle_key(key)
            if save:
                return True
        
        cv2.destroyAllWindows()
        return False

def manual_registration(ir_img, vis_img, global_dx=0, global_dy=0, global_scale_x=1.0, global_scale_y=1.0):
    reg = InteractiveRegistration(ir_img, vis_img, global_dx, global_dy, global_scale_x, global_scale_y)
    saved = reg.run()
    
    if saved:
        h, w = ir_img.shape[:2]
        center = (w // 2, h // 2)
        
        M_scale = cv2.getRotationMatrix2D(center, 0, 1.0)
        M_scale[0, 0] *= reg.scale_x
        M_scale[1, 1] *= reg.scale_y
        M_scale[0, 2] += reg.dx
        M_scale[1, 2] += reg.dy
        
        registered_img = cv2.warpAffine(ir_img, M_scale, (w, h))
        return registered_img, reg.dx, reg.dy, reg.scale_x, reg.scale_y
    else:
        return None, reg.dx, reg.dy, reg.scale_x, reg.scale_y

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    file_list = sorted(os.listdir(R_PATH))
    
    print("交互式图像配准工具")
    print("=" * 50)
    print("控制说明:")
    print("  方向键: 移动红外图像 (仅在Manual模式下)")
    print("  W/E: 水平缩放 (仅在Manual模式下)")
    print("  A/D: 垂直缩放 (仅在Manual模式下)")
    print("  G: 切换 Global/Manual 模式")
    print("  +/-: 调整混合比例")
    print("  S: 保存当前变换参数")
    print("  Q/ESC: 退出")
    print("=" * 50)
    
    global_dx = 0
    global_dy = 0
    global_scale_x = 1.0
    global_scale_y = 1.0
    
    for i, file_name in enumerate(file_list):
        ir_file = os.path.join(R_PATH, file_name)
        vis_file = os.path.join(VIS_PATH, file_name)
        
        if not os.path.exists(vis_file):
            print(f"可见光图像不存在: {vis_file}, 跳过")
            continue
        
        ir_img = cv2.imread(ir_file)
        vis_img = cv2.imread(vis_file)
        
        if ir_img is None or vis_img is None:
            print(f"无法读取图像: {file_name}")
            continue
        
        print(f"\n正在处理: {file_name} ({i+1}/{len(file_list)})")
        print(f"当前全局参数: dx={global_dx}, dy={global_dy}, scale_x={global_scale_x:.3f}, scale_y={global_scale_y:.3f}")
        
        registered_img, dx, dy, scale_x, scale_y = manual_registration(ir_img, vis_img, global_dx, global_dy, global_scale_x, global_scale_y)
        
        if registered_img is not None:
            output_file = os.path.join(OUTPUT_PATH, file_name)
            cv2.imwrite(output_file, registered_img)
            
            global_dx = dx
            global_dy = dy
            global_scale_x = scale_x
            global_scale_y = scale_y
            print(f"已保存参数: dx={dx}, dy={dy}, scale_x={scale_x:.3f}, scale_y={scale_y:.3f}")
        else:
            print(f"跳过: {file_name}")
    
    print(f"\n配准完成! 共处理图像保存在: {OUTPUT_PATH}")
