from __future__ import annotations

from pathlib import Path

import cv2


class InteractiveRegistration:
    def __init__(
        self,
        ir_img,
        vis_img,
        global_dx: int = 0,
        global_dy: int = 0,
        global_scale_x: float = 1.0,
        global_scale_y: float = 1.0,
    ) -> None:
        self.ir_img = ir_img
        self.vis_img = vis_img
        self.dx = global_dx
        self.dy = global_dy
        self.scale_x = global_scale_x
        self.scale_y = global_scale_y
        self.alpha = 0.5
        self.running = True
        self.use_global = True

        height, width = ir_img.shape[:2]
        if vis_img.shape[:2] != (height, width):
            self.vis_img = cv2.resize(vis_img, (width, height))

    def update_display(self) -> None:
        height, width = self.ir_img.shape[:2]
        center = (width // 2, height // 2)

        matrix = cv2.getRotationMatrix2D(center, 0, 1.0)
        matrix[0, 0] *= self.scale_x
        matrix[1, 1] *= self.scale_y
        matrix[0, 2] += self.dx
        matrix[1, 2] += self.dy

        transformed_ir = cv2.warpAffine(self.ir_img, matrix, (width, height))
        blended = cv2.addWeighted(self.vis_img, self.alpha, transformed_ir, 1 - self.alpha, 0)

        display = blended.copy()
        mode_text = "Mode: Global" if self.use_global else "Mode: Manual"
        info_text = (
            f"{mode_text} | Offset: dx={self.dx}, dy={self.dy}, "
            f"ScaleX={self.scale_x:.3f}, ScaleY={self.scale_y:.3f}"
        )
        help_text = "Arrows: Move | W/E: ScaleX | A/D: ScaleY | G: Toggle Mode | +/-: Blend | S: Save | Q: Quit"

        cv2.putText(display, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(display, help_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("Registration", display)

    def handle_key(self, key: int) -> bool:
        if key in (27, ord("q"), ord("Q")):
            self.running = False
            return False

        if key in (ord("s"), ord("S")):
            return True

        if key in (ord("g"), ord("G")):
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
            elif key in (ord("w"), ord("W")):
                self.scale_x = min(2.0, self.scale_x + 0.01)
            elif key in (ord("e"), ord("E")):
                self.scale_x = max(0.5, self.scale_x - 0.01)
            elif key in (ord("d"), ord("D")):
                self.scale_y = min(2.0, self.scale_y + 0.01)
            elif key in (ord("a"), ord("A")):
                self.scale_y = max(0.5, self.scale_y - 0.01)

        if key in (ord("+"), ord("=")):
            self.alpha = min(1.0, self.alpha + 0.1)
        elif key == ord("-"):
            self.alpha = max(0.0, self.alpha - 0.1)

        return False

    def run(self) -> bool:
        cv2.namedWindow("Registration", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Registration", 800, 600)

        while self.running:
            self.update_display()
            key = cv2.waitKeyEx(0) & 0xFFFFFFFF
            should_save = self.handle_key(key)
            if should_save:
                return True

        cv2.destroyAllWindows()
        return False


def manual_registration(
    ir_img,
    vis_img,
    global_dx: int = 0,
    global_dy: int = 0,
    global_scale_x: float = 1.0,
    global_scale_y: float = 1.0,
):
    registration = InteractiveRegistration(
        ir_img,
        vis_img,
        global_dx,
        global_dy,
        global_scale_x,
        global_scale_y,
    )
    saved = registration.run()

    if not saved:
        return None, registration.dx, registration.dy, registration.scale_x, registration.scale_y

    height, width = ir_img.shape[:2]
    center = (width // 2, height // 2)

    matrix = cv2.getRotationMatrix2D(center, 0, 1.0)
    matrix[0, 0] *= registration.scale_x
    matrix[1, 1] *= registration.scale_y
    matrix[0, 2] += registration.dx
    matrix[1, 2] += registration.dy

    registered_img = cv2.warpAffine(ir_img, matrix, (width, height))
    return (
        registered_img,
        registration.dx,
        registration.dy,
        registration.scale_x,
        registration.scale_y,
    )


def run_batch_registration(
    ir_dir: Path | str = Path("imagesIR"),
    visible_dir: Path | str = Path("images"),
    output_dir: Path | str = Path("imagesIR_registered"),
) -> None:
    ir_dir = Path(ir_dir)
    visible_dir = Path(visible_dir)
    output_dir = Path(output_dir)

    if not ir_dir.exists():
        raise FileNotFoundError(f"红外目录不存在: {ir_dir}")
    if not visible_dir.exists():
        raise FileNotFoundError(f"可见光目录不存在: {visible_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    file_list = sorted(path.name for path in ir_dir.iterdir() if path.is_file())

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

    for index, file_name in enumerate(file_list, start=1):
        ir_file = ir_dir / file_name
        vis_file = visible_dir / file_name

        if not vis_file.exists():
            print(f"可见光图像不存在: {vis_file}, 跳过")
            continue

        ir_img = cv2.imread(str(ir_file))
        vis_img = cv2.imread(str(vis_file))

        if ir_img is None or vis_img is None:
            print(f"无法读取图像: {file_name}")
            continue

        print(f"\n正在处理: {file_name} ({index}/{len(file_list)})")
        print(
            "当前全局参数: "
            f"dx={global_dx}, dy={global_dy}, "
            f"scale_x={global_scale_x:.3f}, scale_y={global_scale_y:.3f}"
        )

        registered_img, dx, dy, scale_x, scale_y = manual_registration(
            ir_img,
            vis_img,
            global_dx,
            global_dy,
            global_scale_x,
            global_scale_y,
        )

        if registered_img is None:
            print(f"跳过: {file_name}")
            continue

        output_file = output_dir / file_name
        cv2.imwrite(str(output_file), registered_img)

        global_dx = dx
        global_dy = dy
        global_scale_x = scale_x
        global_scale_y = scale_y
        print(f"已保存参数: dx={dx}, dy={dy}, scale_x={scale_x:.3f}, scale_y={scale_y:.3f}")

    print(f"\n配准完成! 共处理图像保存在: {output_dir}")
