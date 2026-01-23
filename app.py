import sys
import cv2
import numpy as np
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QSlider, QCheckBox, 
                             QGroupBox, QGridLayout, QMessageBox, QScrollArea,
                             QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont

class WheelEventFilter:
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            return True
        return super().eventFilter(obj, event)

class ImageRegistrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像配准工具")
        self.setGeometry(100, 100, 1400, 800)
        
        self.ir_img = None
        self.vis_img = None
        self.ir_dir = None
        self.vis_dir = None
        self.result_dir = None
        self.ir_files = []
        self.vis_files = []
        self.current_index = 0
        self.dx = 0
        self.dy = 0
        self.angle = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.alpha = 0.5
        
        self.dragging = False
        self.last_pos = None
        
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.on_move_timer)
        self.move_dx = 0
        self.move_dy = 0
        
        self.prev_timer = QTimer()
        self.prev_timer.timeout.connect(self.prev_image)
        
        self.next_timer = QTimer()
        self.next_timer.timeout.connect(self.next_image)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 0)
        
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.image_label = QLabel()
        self.image_label.setMinimumSize(900, 700)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.image_mouse_press
        self.image_label.mouseMoveEvent = self.image_mouse_move
        self.image_label.mouseReleaseEvent = self.image_mouse_release
        
        layout.addWidget(self.image_label)
        
        return panel
    
    def create_right_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(450)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        dir_group = QGroupBox("目录设置")
        dir_layout = QGridLayout()
        
        self.load_ir_dir_btn = QPushButton("加载红外目录")
        self.load_ir_dir_btn.clicked.connect(self.load_ir_directory)
        
        self.load_vis_dir_btn = QPushButton("加载可见光目录")
        self.load_vis_dir_btn.clicked.connect(self.load_vis_directory)
        
        self.load_result_dir_btn = QPushButton("加载结果目录")
        self.load_result_dir_btn.clicked.connect(self.load_result_directory)
        
        dir_layout.addWidget(QLabel("红外目录:"), 0, 0)
        dir_layout.addWidget(self.load_ir_dir_btn, 0, 1)
        dir_layout.addWidget(QLabel("可见光目录:"), 1, 0)
        dir_layout.addWidget(self.load_vis_dir_btn, 1, 1)
        dir_layout.addWidget(QLabel("结果目录:"), 2, 0)
        dir_layout.addWidget(self.load_result_dir_btn, 2, 1)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        nav_group = QGroupBox("图像导航")
        nav_layout = QGridLayout()
        
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.pressed.connect(self.on_prev_pressed)
        self.prev_btn.released.connect(self.on_prev_released)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("下一张")
        self.next_btn.pressed.connect(self.on_next_pressed)
        self.next_btn.released.connect(self.on_next_released)
        self.next_btn.setEnabled(False)
        
        self.clear_current_btn = QPushButton("清空当前")
        self.clear_current_btn.clicked.connect(self.clear_current_params)
        self.clear_current_btn.setEnabled(False)
        
        self.clear_all_btn = QPushButton("清空所有")
        self.clear_all_btn.clicked.connect(self.clear_all_params)
        self.clear_all_btn.setEnabled(False)
        
        move_group = QGroupBox("移动控制")
        move_layout = QGridLayout()
        
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.pressed.connect(lambda: self.on_move_pressed(0, -1))
        self.move_up_btn.released.connect(self.on_move_released)
        self.move_up_btn.setEnabled(False)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.pressed.connect(lambda: self.on_move_pressed(0, 1))
        self.move_down_btn.released.connect(self.on_move_released)
        self.move_down_btn.setEnabled(False)
        
        self.move_left_btn = QPushButton("←")
        self.move_left_btn.pressed.connect(lambda: self.on_move_pressed(-1, 0))
        self.move_left_btn.released.connect(self.on_move_released)
        self.move_left_btn.setEnabled(False)
        
        self.move_right_btn = QPushButton("→")
        self.move_right_btn.pressed.connect(lambda: self.on_move_pressed(1, 0))
        self.move_right_btn.released.connect(self.on_move_released)
        self.move_right_btn.setEnabled(False)
        
        move_layout.addWidget(self.move_up_btn, 0, 1)
        move_layout.addWidget(self.move_left_btn, 1, 0)
        move_layout.addWidget(self.move_down_btn, 1, 1)
        move_layout.addWidget(self.move_right_btn, 1, 2)
        
        move_group.setLayout(move_layout)
        
        self.export_btn = QPushButton("批量导出")
        self.export_btn.clicked.connect(self.export_images)
        self.export_btn.setEnabled(False)
        
        nav_layout.addWidget(self.prev_btn, 0, 0)
        nav_layout.addWidget(self.next_btn, 0, 1)
        nav_layout.addWidget(self.clear_current_btn, 1, 0)
        nav_layout.addWidget(self.clear_all_btn, 1, 1)
        nav_layout.addWidget(self.export_btn, 2, 0, 1, 2)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(move_group)
        layout.addWidget(nav_group)
        
        offset_group = QGroupBox("偏移量")
        offset_layout = QGridLayout()
        
        self.dx_label = QLabel("dx: 0")
        self.dy_label = QLabel("dy: 0")
        self.angle_label = QLabel("Angle: 0.0°")
        
        offset_layout.addWidget(QLabel("X偏移:"), 0, 0)
        offset_layout.addWidget(self.dx_label, 0, 1)
        offset_layout.addWidget(QLabel("Y偏移:"), 1, 0)
        offset_layout.addWidget(self.dy_label, 1, 1)
        offset_layout.addWidget(QLabel("旋转:"), 2, 0)
        offset_layout.addWidget(self.angle_label, 2, 1)
        
        offset_group.setLayout(offset_layout)
        layout.addWidget(offset_group)
        
        rotate_group = QGroupBox("旋转")
        rotate_layout = QVBoxLayout()
        
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        self.angle_slider.valueChanged.connect(self.on_angle_changed)
        
        rotate_layout.addWidget(self.angle_label)
        rotate_layout.addWidget(self.angle_slider)
        
        rotate_group.setLayout(rotate_layout)
        layout.addWidget(rotate_group)
        
        scale_group = QGroupBox("缩放")
        scale_layout = QGridLayout()
        
        self.scale_x_label = QLabel("ScaleX: 1.000")
        self.scale_y_label = QLabel("ScaleY: 1.000")
        
        self.scale_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_x_slider.setRange(50, 200)
        self.scale_x_slider.setValue(100)
        self.scale_x_slider.valueChanged.connect(self.on_scale_x_changed)
        
        self.scale_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_y_slider.setRange(50, 200)
        self.scale_y_slider.setValue(100)
        self.scale_y_slider.valueChanged.connect(self.on_scale_y_changed)
        
        scale_layout.addWidget(QLabel("X缩放:"), 0, 0)
        scale_layout.addWidget(self.scale_x_label, 0, 1)
        scale_layout.addWidget(self.scale_x_slider, 1, 0, 1, 2)
        scale_layout.addWidget(QLabel("Y缩放:"), 2, 0)
        scale_layout.addWidget(self.scale_y_label, 2, 1)
        scale_layout.addWidget(self.scale_y_slider, 3, 0, 1, 2)
        
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        blend_group = QGroupBox("混合比例")
        blend_layout = QVBoxLayout()
        
        self.alpha_label = QLabel("Alpha: 0.5")
        
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(50)
        self.alpha_slider.valueChanged.connect(self.on_alpha_changed)
        
        blend_layout.addWidget(self.alpha_label)
        blend_layout.addWidget(self.alpha_slider)
        
        blend_group.setLayout(blend_layout)
        layout.addWidget(blend_group)
        
        info_group = QGroupBox("信息")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel("请加载红外和可见光目录")
        self.info_label.setWordWrap(True)
        
        info_layout.addWidget(self.info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        help_group = QGroupBox("操作说明")
        help_layout = QVBoxLayout()
        
        help_text = QLabel()
        help_text.setTextFormat(Qt.TextFormat.RichText)
        help_text.setWordWrap(True)
        help_text.setText("""
<b>键盘控制:</b>
• 方向键 ← → ↑ ↓: 移动红外图像
• W / E: 水平缩放 (放大/缩小)
• A / D: 垂直缩放 (缩小/放大)

<b>滑块控制:</b>
• X缩放滑块: 精确调整水平缩放 (0.5x - 2.0x)
• Y缩放滑块: 精确调整垂直缩放 (0.5x - 2.0x)
• 旋转滑块: 调整旋转角度 (-180° - 180°)
• Alpha滑块: 调整混合比例 (0.0 - 1.0)

<b>文件操作:</b>
• 加载目录: 批量加载图像（支持多级目录），使用上一张/下一张切换
• 加载结果目录: 选择保存参数的目录
• 批量导出: 将所有图像配准并导出到指定目录（保持目录结构）

<b>提示:</b>
• 红外图像为红色调，可见光图像为正常颜色
• 调整混合比例可以更清楚地看到对齐效果
• 点击下一张会自动保存当前参数到results目录
• 参数在切换图像时保持不变
• 批量导出会使用当前参数处理所有图像
• 支持多级目录结构，导出时会保持原有的目录结构
""")
        
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        layout.addStretch()
        
        scroll.setWidget(panel)
        return scroll
    
    def load_ir_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择红外图像目录", ""
        )
        
        if dir_path:
            self.ir_dir = Path(dir_path)
            self.ir_files = sorted([f for f in self.ir_dir.rglob('*') 
                                 if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
            
            if self.ir_files:
                self.current_index = 0
                self.load_current_images()
                self.info_label.setText(f"已加载红外目录: {dir_path}\n共 {len(self.ir_files)} 张图像")
                self.update_nav_buttons()
                self.check_export_enabled()
            else:
                QMessageBox.warning(self, "警告", "目录中没有找到图像文件")
    
    def load_vis_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择可见光图像目录", ""
        )
        
        if dir_path:
            self.vis_dir = Path(dir_path)
            self.vis_files = sorted([f for f in self.vis_dir.rglob('*') 
                                  if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
            
            if self.vis_files:
                self.current_index = 0
                self.load_current_images()
                self.info_label.setText(f"已加载可见光目录: {dir_path}\n共 {len(self.vis_files)} 张图像")
                self.update_nav_buttons()
                self.check_export_enabled()
            else:
                QMessageBox.warning(self, "警告", "目录中没有找到图像文件")
    
    def load_result_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择结果目录", ""
        )
        
        if dir_path:
            self.result_dir = Path(dir_path)
            self.info_label.setText(f"已设置结果目录: {dir_path}")
    
    def load_current_images(self):
        if self.ir_files and self.current_index < len(self.ir_files):
            self.ir_img = cv2.imread(str(self.ir_files[self.current_index]))
        
        if self.vis_files and self.current_index < len(self.vis_files):
            self.vis_img = cv2.imread(str(self.vis_files[self.current_index]))
        
        self.update_display()
        self.load_image_params()
    
    def load_image_params(self):
        if self.result_dir is None or not self.ir_files:
            return
        
        current_file = self.ir_files[self.current_index]
        json_file = self.result_dir / f"{current_file.stem}.json"
        
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                    self.dx = params.get('dx', 0)
                    self.dy = params.get('dy', 0)
                    self.angle = params.get('angle', 0.0)
                    self.scale_x = params.get('scale_x', 1.0)
                    self.scale_y = params.get('scale_y', 1.0)
                    
                    self.update_info_labels()
                    self.info_label.setText(f"已加载参数: dx={self.dx}, dy={self.dy}, angle={self.angle:.1f}°, scale_x={self.scale_x:.3f}, scale_y={self.scale_y:.3f}")
            except Exception as e:
                print(f"加载参数失败: {e}")
    
    def prev_image(self, save_params=True):
        if save_params and self.ir_img is not None and self.vis_img is not None:
            self.auto_save_params()
        
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_images()
            self.info_label.setText(f"当前图像: {self.current_index + 1}/{max(len(self.ir_files), len(self.vis_files))}")
            self.update_nav_buttons()
    
    def next_image(self, save_params=True):
        if save_params and self.ir_img is not None and self.vis_img is not None:
            self.auto_save_params()
        
        max_index = max(len(self.ir_files), len(self.vis_files))
        if self.current_index < max_index - 1:
            self.current_index += 1
            self.load_current_images()
            self.info_label.setText(f"当前图像: {self.current_index + 1}/{max_index}")
            self.update_nav_buttons()
    
    def update_nav_buttons(self):
        max_index = max(len(self.ir_files), len(self.vis_files))
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < max_index - 1 and max_index > 0)
        
        move_enabled = self.ir_img is not None and self.vis_img is not None
        self.move_up_btn.setEnabled(move_enabled)
        self.move_down_btn.setEnabled(move_enabled)
        self.move_left_btn.setEnabled(move_enabled)
        self.move_right_btn.setEnabled(move_enabled)
        
        clear_enabled = self.result_dir is not None
        self.clear_current_btn.setEnabled(clear_enabled)
        self.clear_all_btn.setEnabled(clear_enabled)
    
    def check_export_enabled(self):
        self.export_btn.setEnabled(len(self.ir_files) > 0 and len(self.vis_files) > 0 and self.result_dir is not None)
    
    def on_prev_pressed(self):
        self.prev_image(save_params=False)
        self.prev_timer.start(200)
    
    def on_prev_released(self):
        self.prev_timer.stop()
    
    def on_next_pressed(self):
        self.next_image(save_params=False)
        self.next_timer.start(200)
    
    def on_next_released(self):
        self.next_timer.stop()
        if self.ir_img is not None and self.vis_img is not None:
            self.auto_save_params()
    
    def on_move_pressed(self, dx, dy):
        self.move_dx = dx
        self.move_dy = dy
        self.manual_move(dx, dy)
        self.move_timer.start(50)
    
    def on_move_released(self):
        self.move_timer.stop()
        self.move_dx = 0
        self.move_dy = 0
    
    def on_move_timer(self):
        self.manual_move(self.move_dx, self.move_dy)
    
    def manual_move(self, dx, dy):
        self.dx += dx
        self.dy += dy
        self.update_info_labels()
        self.update_display()
    
    def clear_current_params(self):
        self.dx = 0
        self.dy = 0
        self.angle = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        self.scale_x_slider.setValue(100)
        self.scale_y_slider.setValue(100)
        self.angle_slider.setValue(0)
        
        self.update_info_labels()
        if self.ir_img is not None and self.vis_img is not None:
            self.update_display()
        
        if self.result_dir is not None and self.ir_files:
            current_file = self.ir_files[self.current_index]
            json_file = self.result_dir / f"{current_file.stem}.json"
            if json_file.exists():
                json_file.unlink()
                self.info_label.setText(f"已清空当前图像配准信息")
        else:
            self.info_label.setText(f"已重置参数")
    
    def clear_all_params(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有图像的配准信息吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        if self.result_dir is not None and self.result_dir.exists():
            for json_file in self.result_dir.glob('*.json'):
                json_file.unlink()
            
            self.dx = 0
            self.dy = 0
            self.angle = 0.0
            self.scale_x = 1.0
            self.scale_y = 1.0
            
            self.scale_x_slider.setValue(100)
            self.scale_y_slider.setValue(100)
            self.angle_slider.setValue(0)
            
            self.update_info_labels()
            self.update_display()
            
            self.info_label.setText(f"已清空所有配准信息")
    
    def update_display(self):
        if self.ir_img is None or self.vis_img is None:
            return
        
        h, w = self.ir_img.shape[:2]
        
        if self.vis_img.shape[:2] != (h, w):
            self.vis_img = cv2.resize(self.vis_img, (w, h))
        
        center = (w // 2, h // 2)
        
        M_scale = cv2.getRotationMatrix2D(center, self.angle, 1.0)
        M_scale[0, 0] *= self.scale_x
        M_scale[1, 1] *= self.scale_y
        M_scale[0, 2] += self.dx
        M_scale[1, 2] += self.dy
        
        transformed_ir = cv2.warpAffine(self.ir_img, M_scale, (w, h))
        
        blended = cv2.addWeighted(self.vis_img, self.alpha, transformed_ir, 1 - self.alpha, 0)
        
        rgb_image = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
        h_img, w_img, ch = rgb_image.shape
        bytes_per_line = ch * w_img
        q_image = QImage(rgb_image.data, w_img, h_img, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    
    def on_scale_x_changed(self, value):
        self.scale_x = value / 100.0
        self.scale_x_label.setText(f"ScaleX: {self.scale_x:.3f}")
        self.update_display()
    
    def on_scale_y_changed(self, value):
        self.scale_y = value / 100.0
        self.scale_y_label.setText(f"ScaleY: {self.scale_y:.3f}")
        self.update_display()
    
    def on_alpha_changed(self, value):
        self.alpha = value / 100.0
        self.alpha_label.setText(f"Alpha: {self.alpha:.2f}")
        self.update_display()
    
    def on_angle_changed(self, value):
        self.angle = float(value)
        self.angle_label.setText(f"Angle: {self.angle:.1f}°")
        self.update_display()
    
    def auto_save_params(self):
        if not self.ir_files or self.result_dir is None:
            return
        
        current_file = self.ir_files[self.current_index]
        json_file = self.result_dir / f"{current_file.stem}.json"
        
        is_default = (self.dx == 0 and self.dy == 0 and 
                     self.angle == 0.0 and 
                     self.scale_x == 1.0 and self.scale_y == 1.0)
        
        if is_default:
            if json_file.exists():
                json_file.unlink()
            return
        
        params = {
            'dx': int(self.dx),
            'dy': int(self.dy),
            'angle': float(self.angle),
            'scale_x': float(self.scale_x),
            'scale_y': float(self.scale_y)
        }
        
        json_file.parent.mkdir(parents=True, exist_ok=True)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
    
    def keyPressEvent(self, event):
        
        key = event.key()
        
        if key == Qt.Key.Key_Left:
            self.dx -= 1
        elif key == Qt.Key.Key_Right:
            self.dx += 1
        elif key == Qt.Key.Key_Up:
            self.dy -= 1
        elif key == Qt.Key.Key_Down:
            self.dy += 1
        elif key == Qt.Key.Key_W:
            self.scale_x = min(2.0, self.scale_x + 0.01)
            self.scale_x_slider.setValue(int(self.scale_x * 100))
        elif key == Qt.Key.Key_E:
            self.scale_x = max(0.5, self.scale_x - 0.01)
            self.scale_x_slider.setValue(int(self.scale_x * 100))
        elif key == Qt.Key.Key_A:
            self.scale_y = max(0.5, self.scale_y - 0.01)
            self.scale_y_slider.setValue(int(self.scale_y * 100))
        elif key == Qt.Key.Key_D:
            self.scale_y = min(2.0, self.scale_y + 0.01)
            self.scale_y_slider.setValue(int(self.scale_y * 100))
        else:
            return
        
        self.update_info_labels()
        self.update_display()
    
    def update_info_labels(self):
        self.dx_label.setText(f"dx: {self.dx}")
        self.dy_label.setText(f"dy: {self.dy}")
        self.angle_label.setText(f"Angle: {self.angle:.1f}°")
        self.scale_x_label.setText(f"ScaleX: {self.scale_x:.3f}")
        self.scale_y_label.setText(f"ScaleY: {self.scale_y:.3f}")
    
    def image_mouse_press(self, event):
        self.dragging = True
        self.last_pos = event.position()
    
    def image_mouse_move(self, event):
        if not self.dragging or self.last_pos is None:
            return
        
        pos = event.position()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        
        self.dx += dx
        self.dy += dy
        
        self.last_pos = pos
        self.update_info_labels()
        self.update_display()
    
    def image_mouse_release(self, event):
        self.dragging = False
        self.last_pos = None
    
    def export_images(self):
        if not self.ir_files or not self.vis_files:
            QMessageBox.warning(self, "警告", "请先加载红外和可见光目录")
            return
        
        if self.result_dir is None:
            QMessageBox.warning(self, "警告", "请先设置结果目录")
            return
        
        export_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录", ""
        )
        
        if not export_dir:
            return
        
        export_path = Path(export_dir)
        
        reply = QMessageBox.question(
            self, "确认导出",
            f"将使用当前参数批量导出所有图像到:\n{export_path}\n\n"
            f"当前参数:\n"
            f"dx={self.dx}, dy={self.dy}\n"
            f"angle={self.angle:.1f}°\n"
            f"scale_x={self.scale_x:.3f}, scale_y={self.scale_y:.3f}\n\n"
            f"共 {len(self.ir_files)} 张图像",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        progress = QProgressBar()
        progress.setRange(0, len(self.ir_files))
        progress.setWindowTitle("导出进度")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.installEventFilter(WheelEventFilter(progress))
        progress.show()
        
        success_count = 0
        fail_count = 0
        
        for i, ir_file in enumerate(self.ir_files):
            progress.setValue(i)
            QApplication.processEvents()
            
            rel_path = ir_file.relative_to(self.ir_dir)
            vis_file = self.vis_dir / rel_path
            
            if not vis_file.exists():
                fail_count += 1
                continue
            
            ir_img = cv2.imread(str(ir_file))
            vis_img = cv2.imread(str(vis_file))
            
            if ir_img is None or vis_img is None:
                fail_count += 1
                continue
            
            h, w = ir_img.shape[:2]
            
            if vis_img.shape[:2] != (h, w):
                vis_img = cv2.resize(vis_img, (w, h))
            
            center = (w // 2, h // 2)
            
            M_scale = cv2.getRotationMatrix2D(center, self.angle, 1.0)
            M_scale[0, 0] *= self.scale_x
            M_scale[1, 1] *= self.scale_y
            M_scale[0, 2] += self.dx
            M_scale[1, 2] += self.dy
            
            registered_img = cv2.warpAffine(ir_img, M_scale, (w, h))
            
            output_file = export_path / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_file), registered_img)
            
            success_count += 1
        
        progress.setValue(len(self.ir_files))
        progress.close()
        
        QMessageBox.information(self, "导出完成", 
            f"成功导出: {success_count} 张\n"
            f"失败: {fail_count} 张\n"
            f"输出目录: {export_path}")

def main():
    app = QApplication(sys.argv)
    window = ImageRegistrationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
