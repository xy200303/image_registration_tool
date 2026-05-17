import sys
import cv2
import numpy as np
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QSlider, QGroupBox, 
                             QGridLayout, QMessageBox, QScrollArea, QProgressBar, QProgressDialog,
                             QCheckBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QKeyEvent, QMouseEvent

from .io import read_image, write_image


class ImageCanvas(QWidget):
    parameters_changed = pyqtSignal(int, int, float, float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: black;")
        self.setMouseTracking(True)
        
        self.ir_image = None
        self.vis_image = None
        self.blended_image = None
        
        self.dx = 0
        self.dy = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.angle = 0.0
        self.alpha = 0.5
        
        self.dragging = False
        self.last_pos = QPoint()
        
    def set_images(self, ir_img, vis_img):
        self.ir_image = ir_img
        self.vis_image = vis_img
        
        if ir_img is not None and vis_img is not None:
            h, w = ir_img.shape[:2]
            if vis_img.shape[:2] != (h, w):
                self.vis_image = cv2.resize(vis_img, (w, h))
        
        self.update_transformed_image()
        
    def update_transformed_image(self):
        if self.ir_image is None or self.vis_image is None:
            self.blended_image = None
            self.update()
            return
        
        h, w = self.ir_image.shape[:2]
        center = (w // 2, h // 2)
        
        M_scale = cv2.getRotationMatrix2D(center, self.angle, 1.0)
        M_scale[0, 0] *= self.scale_x
        M_scale[1, 1] *= self.scale_y
        M_scale[0, 2] += self.dx
        M_scale[1, 2] += self.dy
        
        transformed_ir = cv2.warpAffine(self.ir_image, M_scale, (w, h))
        
        blended = cv2.addWeighted(self.vis_image, self.alpha, transformed_ir, 1 - self.alpha, 0)
        self.blended_image = blended
        
        self.update()
        
    def set_parameters(self, dx, dy, scale_x, scale_y, angle, alpha):
        self.dx = dx
        self.dy = dy
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.angle = angle
        self.alpha = alpha
        self.update_transformed_image()
        
    def get_parameters(self):
        return self.dx, self.dy, self.scale_x, self.scale_y, self.angle, self.alpha
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if self.blended_image is not None:
            rgb_image = cv2.cvtColor(self.blended_image, cv2.COLOR_BGR2RGB)
            h_img, w_img, ch = rgb_image.shape
            bytes_per_line = ch * w_img
            q_image = QImage(rgb_image.data, w_img, h_img, bytes_per_line, QImage.Format.Format_RGB888)
            
            pixmap = QPixmap.fromImage(q_image)
            
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请加载红外和可见光图像")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_pos = event.position()
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            pos = event.position()
            dx = int(pos.x() - self.last_pos.x())
            dy = int(pos.y() - self.last_pos.y())
            
            self.dx += dx
            self.dy += dy
            self.last_pos = pos
            
            self.update_transformed_image()
            self.parameters_changed.emit(self.dx, self.dy, self.scale_x, self.scale_y, self.angle)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False


class ImageRegistrationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像配准工具 - PyQt6")
        self.setGeometry(100, 100, 1200, 800)
        
        self.ir_dir = None
        self.vis_dir = None
        self.result_dir = Path.cwd() / "results"
        self.result_dir.mkdir(exist_ok=True)
        self.ir_files = []
        self.vis_files = []
        self.current_index = 0
        
        self.use_global_mode = True
        self.global_dx = 0
        self.global_dy = 0
        self.global_scale_x = 1.0
        self.global_scale_y = 1.0
        
        self.next_btn_timer = None
        self.next_btn_long_press_threshold = 500
        self.next_btn_auto_switch_interval = 300
        self.next_btn_is_long_press = False
        
        self.pressed_keys = set()
        self.key_repeat_timer = QTimer()
        self.key_repeat_timer.timeout.connect(self.on_key_repeat)
        self.key_repeat_interval = 50
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()
        
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)
        
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.image_canvas = ImageCanvas(self)
        self.image_canvas.parameters_changed.connect(self.update_parameter_labels)
        
        layout.addWidget(self.image_canvas)
        
        return panel
        
    def create_right_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(350)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        dir_group = QGroupBox("目录设置")
        dir_layout = QGridLayout()
        
        self.load_ir_btn = QPushButton("加载红外目录")
        self.load_ir_btn.clicked.connect(self.load_ir_directory)
        
        self.load_vis_btn = QPushButton("加载可见光目录")
        self.load_vis_btn.clicked.connect(self.load_vis_directory)
        
        self.load_result_btn = QPushButton("加载结果目录")
        self.load_result_btn.clicked.connect(self.load_result_directory)
        
        dir_layout.addWidget(QLabel("红外:"), 0, 0)
        dir_layout.addWidget(self.load_ir_btn, 0, 1)
        dir_layout.addWidget(QLabel("可见光:"), 1, 0)
        dir_layout.addWidget(self.load_vis_btn, 1, 1)
        dir_layout.addWidget(QLabel("结果:"), 2, 0)
        dir_layout.addWidget(self.load_result_btn, 2, 1)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        mode_group = QGroupBox("模式选择")
        mode_layout = QVBoxLayout()
        
        self.global_mode_cb = QCheckBox("使用全局参数模式")
        self.global_mode_cb.setChecked(True)
        self.global_mode_cb.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.global_mode_cb)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        keyboard_group = QGroupBox("移动控制")
        keyboard_layout = QGridLayout()
        keyboard_layout.setSpacing(5)
        
        self.key_up_btn = QPushButton("↑")
        self.key_up_btn.setFixedSize(40, 40)
        self.key_up_btn.pressed.connect(lambda: self.simulate_key_press(Qt.Key.Key_Up))
        self.key_up_btn.released.connect(lambda: self.simulate_key_release(Qt.Key.Key_Up))
        
        self.key_down_btn = QPushButton("↓")
        self.key_down_btn.setFixedSize(40, 40)
        self.key_down_btn.pressed.connect(lambda: self.simulate_key_press(Qt.Key.Key_Down))
        self.key_down_btn.released.connect(lambda: self.simulate_key_release(Qt.Key.Key_Down))
        
        self.key_left_btn = QPushButton("←")
        self.key_left_btn.setFixedSize(40, 40)
        self.key_left_btn.pressed.connect(lambda: self.simulate_key_press(Qt.Key.Key_Left))
        self.key_left_btn.released.connect(lambda: self.simulate_key_release(Qt.Key.Key_Left))
        
        self.key_right_btn = QPushButton("→")
        self.key_right_btn.setFixedSize(40, 40)
        self.key_right_btn.pressed.connect(lambda: self.simulate_key_press(Qt.Key.Key_Right))
        self.key_right_btn.released.connect(lambda: self.simulate_key_release(Qt.Key.Key_Right))
        
        keyboard_layout.addWidget(self.key_up_btn, 0, 1)
        keyboard_layout.addWidget(self.key_left_btn, 1, 0)
        keyboard_layout.addWidget(self.key_down_btn, 1, 1)
        keyboard_layout.addWidget(self.key_right_btn, 1, 2)
        
        keyboard_group.setLayout(keyboard_layout)
        layout.addWidget(keyboard_group)
        
        nav_group = QGroupBox("图像导航")
        nav_layout = QGridLayout()
        
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("下一张")
        self.next_btn.pressed.connect(self.next_btn_pressed)
        self.next_btn.released.connect(self.next_btn_released)
        self.next_btn.setEnabled(False)
        
        self.save_btn = QPushButton("保存参数")
        self.save_btn.clicked.connect(self.save_parameters)
        self.save_btn.setEnabled(False)

        self.auto_optimize_btn = QPushButton("一键自动优化")
        self.auto_optimize_btn.clicked.connect(self.auto_optimize_current_image)
        self.auto_optimize_btn.setEnabled(False)

        self.batch_optimize_btn = QPushButton("批量自动优化")
        self.batch_optimize_btn.clicked.connect(self.batch_auto_optimize)
        self.batch_optimize_btn.setEnabled(False)
        
        self.export_btn = QPushButton("批量导出")
        self.export_btn.clicked.connect(self.export_images)
        self.export_btn.setEnabled(False)
        
        self.clear_current_btn = QPushButton("清空当前")
        self.clear_current_btn.clicked.connect(self.clear_current_params)
        self.clear_current_btn.setEnabled(False)
        
        self.clear_all_btn = QPushButton("清空所有")
        self.clear_all_btn.clicked.connect(self.clear_all_params)
        self.clear_all_btn.setEnabled(False)
        
        nav_layout.addWidget(self.prev_btn, 0, 0)
        nav_layout.addWidget(self.next_btn, 0, 1)
        nav_layout.addWidget(self.save_btn, 1, 0, 1, 2)
        nav_layout.addWidget(self.auto_optimize_btn, 2, 0, 1, 2)
        nav_layout.addWidget(self.batch_optimize_btn, 3, 0, 1, 2)
        nav_layout.addWidget(self.export_btn, 4, 0, 1, 2)
        nav_layout.addWidget(self.clear_current_btn, 5, 0)
        nav_layout.addWidget(self.clear_all_btn, 5, 1)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        offset_group = QGroupBox("偏移量")
        offset_layout = QGridLayout()
        
        self.dx_spin = QSpinBox()
        self.dx_spin.setRange(-1000, 1000)
        self.dx_spin.valueChanged.connect(self.on_dx_changed)
        
        self.dy_spin = QSpinBox()
        self.dy_spin.setRange(-1000, 1000)
        self.dy_spin.valueChanged.connect(self.on_dy_changed)
        
        offset_layout.addWidget(QLabel("dx:"), 0, 0)
        offset_layout.addWidget(self.dx_spin, 0, 1)
        offset_layout.addWidget(QLabel("dy:"), 1, 0)
        offset_layout.addWidget(self.dy_spin, 1, 1)
        
        offset_group.setLayout(offset_layout)
        layout.addWidget(offset_group)
        
        scale_group = QGroupBox("缩放")
        scale_layout = QGridLayout()
        
        self.scale_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_x_slider.setRange(50, 200)
        self.scale_x_slider.setValue(100)
        self.scale_x_slider.valueChanged.connect(self.on_scale_x_changed)
        
        self.scale_x_label = QLabel("ScaleX: 1.00")
        
        self.scale_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_y_slider.setRange(50, 200)
        self.scale_y_slider.setValue(100)
        self.scale_y_slider.valueChanged.connect(self.on_scale_y_changed)
        
        self.scale_y_label = QLabel("ScaleY: 1.00")
        
        scale_layout.addWidget(QLabel("X缩放:"), 0, 0)
        scale_layout.addWidget(self.scale_x_label, 0, 1)
        scale_layout.addWidget(self.scale_x_slider, 1, 0, 1, 2)
        scale_layout.addWidget(QLabel("Y缩放:"), 2, 0)
        scale_layout.addWidget(self.scale_y_label, 2, 1)
        scale_layout.addWidget(self.scale_y_slider, 3, 0, 1, 2)
        
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        rotate_group = QGroupBox("旋转")
        rotate_layout = QVBoxLayout()
        
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        self.angle_slider.valueChanged.connect(self.on_angle_changed)
        
        self.angle_label = QLabel("Angle: 0.0°")
        
        rotate_layout.addWidget(self.angle_label)
        rotate_layout.addWidget(self.angle_slider)
        
        rotate_group.setLayout(rotate_layout)
        layout.addWidget(rotate_group)
        
        blend_group = QGroupBox("混合比例")
        blend_layout = QVBoxLayout()
        
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(50)
        self.alpha_slider.valueChanged.connect(self.on_alpha_changed)
        
        self.alpha_label = QLabel("Alpha: 0.50")
        
        blend_layout.addWidget(self.alpha_label)
        blend_layout.addWidget(self.alpha_slider)
        
        blend_group.setLayout(blend_layout)
        layout.addWidget(blend_group)
        
        info_group = QGroupBox("信息")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel("请加载红外和可见光目录\n结果目录: results")
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
• 方向键: 移动红外图像 (Manual模式，支持长按连续移动)
• W/E: 水平缩放 (Manual模式，支持长按连续调整)
• A/D: 垂直缩放 (Manual模式，支持长按连续调整)
• +/-: 调整混合比例
• S: 保存当前参数
• Q/ESC: 退出

<b>鼠标控制:</b>
• 拖拽: 移动红外图像

<b>自动优化:</b>
• 一键自动优化当前图像的 dx / dy / scale_x / scale_y
• 批量自动优化会对整个目录逐张拟合并保存参数
• 自动优化会保持当前旋转角度不变

<b>模式说明:</b>
• Global模式: 使用全局参数，适用于批量处理
• Manual模式: 手动调整每张图像的参数
        """)
        
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        layout.addStretch()
        
        scroll.setWidget(panel)
        return scroll
        
    def load_ir_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择红外图像目录", "")
        
        if dir_path:
            self.ir_dir = Path(dir_path)
            self.ir_files = sorted([f for f in self.ir_dir.rglob('*') 
                                   if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
            
            if self.ir_files:
                self.current_index = 0
                self.load_current_images()
                self.info_label.setText(f"已加载红外目录: {dir_path}\n共 {len(self.ir_files)} 张图像")
                self.update_nav_buttons()
            else:
                QMessageBox.warning(self, "警告", "目录中没有找到图像文件")
                
    def load_vis_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择可见光图像目录", "")
        
        if dir_path:
            self.vis_dir = Path(dir_path)
            self.vis_files = sorted([f for f in self.vis_dir.rglob('*') 
                                    if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']])
            
            if self.vis_files:
                self.current_index = 0
                self.load_current_images()
                self.info_label.setText(f"已加载可见光目录: {dir_path}\n共 {len(self.vis_files)} 张图像")
                self.update_nav_buttons()
            else:
                QMessageBox.warning(self, "警告", "目录中没有找到图像文件")
                
    def load_result_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择结果目录", str(self.result_dir))
        
        if dir_path:
            self.result_dir = Path(dir_path)
            self.info_label.setText(f"已设置结果目录: {dir_path}")
            
    def load_current_images(self):
        if self.ir_files and self.current_index < len(self.ir_files):
            ir_img = read_image(self.ir_files[self.current_index])
        else:
            ir_img = None
            
        if self.vis_files and self.current_index < len(self.vis_files):
            vis_img = read_image(self.vis_files[self.current_index])
        else:
            vis_img = None
            
        self.image_canvas.set_images(ir_img, vis_img)
        self.load_image_params()

    def get_result_json_path(self, ir_file):
        return self.result_dir / f"{ir_file.stem}.json"

    def get_visible_file_for_ir(self, ir_file):
        if self.ir_dir is None or self.vis_dir is None:
            return None

        rel_path = ir_file.relative_to(self.ir_dir)
        vis_file = self.vis_dir / rel_path
        if vis_file.exists():
            return vis_file
        return None

    def build_params_dict(self, dx, dy, angle, scale_x, scale_y):
        return {
            'dx': int(dx),
            'dy': int(dy),
            'angle': float(angle),
            'scale_x': float(scale_x),
            'scale_y': float(scale_y)
        }

    def read_params_for_file(self, ir_file):
        json_file = self.get_result_json_path(ir_file)

        if not json_file.exists():
            return None

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                params = json.load(f)
        except Exception as e:
            print(f"加载参数失败: {e}")
            return None

        return self.build_params_dict(
            params.get('dx', 0),
            params.get('dy', 0),
            params.get('angle', 0.0),
            params.get('scale_x', 1.0),
            params.get('scale_y', 1.0),
        )

    def write_params_for_file(self, ir_file, dx, dy, angle, scale_x, scale_y):
        json_file = self.get_result_json_path(ir_file)
        params = self.build_params_dict(dx, dy, angle, scale_x, scale_y)
        json_file.parent.mkdir(parents=True, exist_ok=True)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        return json_file
        
    def load_image_params(self):
        if not self.ir_files:
            return
        
        current_file = self.ir_files[self.current_index]
        params = self.read_params_for_file(current_file)

        if params is not None:
            dx = params['dx']
            dy = params['dy']
            angle = params['angle']
            scale_x = params['scale_x']
            scale_y = params['scale_y']

            self.set_parameter_controls(dx, dy, scale_x, scale_y, angle)
            self.info_label.setText(
                f"已加载参数: dx={dx}, dy={dy}, angle={angle:.1f}°, "
                f"scale_x={scale_x:.3f}, scale_y={scale_y:.3f}"
            )
                
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_images()
            self.info_label.setText(f"当前图像: {self.current_index + 1}/{max(len(self.ir_files), len(self.vis_files))}")
            self.update_nav_buttons()
            
    def next_btn_pressed(self):
        self.next_btn_is_long_press = False
        self.next_btn_timer = QTimer()
        self.next_btn_timer.setSingleShot(True)
        self.next_btn_timer.timeout.connect(self.on_next_btn_long_press)
        self.next_btn_timer.start(self.next_btn_long_press_threshold)
        
    def next_btn_released(self):
        if self.next_btn_timer:
            self.next_btn_timer.stop()
            self.next_btn_timer = None
        
        if not self.next_btn_is_long_press:
            self.next_image()
        
        self.next_btn_is_long_press = False
        
    def on_next_btn_long_press(self):
        self.next_btn_is_long_press = True
        self.next_image()
        self.start_auto_switch()
        
    def start_auto_switch(self):
        self.next_btn_timer = QTimer()
        self.next_btn_timer.timeout.connect(self.auto_switch_next)
        self.next_btn_timer.start(self.next_btn_auto_switch_interval)
        
    def auto_switch_next(self):
        self.next_image()
            
    def next_image(self):
        max_index = max(len(self.ir_files), len(self.vis_files))
        if self.current_index < max_index - 1:
            self.save_parameters(show_message=False)
            self.current_index += 1
            self.load_current_images()
            self.info_label.setText(f"当前图像: {self.current_index + 1}/{max_index}")
            self.update_nav_buttons()
        else:
            if self.next_btn_is_long_press and self.next_btn_timer:
                self.next_btn_timer.stop()
                self.next_btn_timer = None
                self.next_btn_is_long_press = False
            
    def update_nav_buttons(self):
        max_index = max(len(self.ir_files), len(self.vis_files))
        has_both_images = len(self.ir_files) > 0 and len(self.vis_files) > 0
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < max_index - 1 and max_index > 0)
        self.save_btn.setEnabled(len(self.ir_files) > 0)
        self.auto_optimize_btn.setEnabled(has_both_images)
        self.batch_optimize_btn.setEnabled(has_both_images)
        self.export_btn.setEnabled(has_both_images)
        self.clear_current_btn.setEnabled(len(self.ir_files) > 0)
        self.clear_all_btn.setEnabled(True)
        
    def clear_current_params(self):
        self.dx_spin.setValue(0)
        self.dy_spin.setValue(0)
        self.angle_slider.setValue(0)
        self.scale_x_slider.setValue(100)
        self.scale_y_slider.setValue(100)
        
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
        
        if self.result_dir.exists():
            for json_file in self.result_dir.glob('*.json'):
                json_file.unlink()
            
            self.dx_spin.setValue(0)
            self.dy_spin.setValue(0)
            self.angle_slider.setValue(0)
            self.scale_x_slider.setValue(100)
            self.scale_y_slider.setValue(100)
            
            self.info_label.setText(f"已清空所有配准信息")
            QMessageBox.information(self, "清空完成", "所有图像的配准信息已清空")
        
    def on_mode_changed(self, checked):
        self.use_global_mode = checked
        mode_text = "Global" if checked else "Manual"
        self.info_label.setText(f"模式切换为: {mode_text}")
        
    def on_dx_changed(self, value):
        self.update_canvas_parameters()
        
    def on_dy_changed(self, value):
        self.update_canvas_parameters()
        
    def on_scale_x_changed(self, value):
        scale_x = value / 100.0
        self.scale_x_label.setText(f"ScaleX: {scale_x:.2f}")
        self.update_canvas_parameters()
        
    def on_scale_y_changed(self, value):
        scale_y = value / 100.0
        self.scale_y_label.setText(f"ScaleY: {scale_y:.2f}")
        self.update_canvas_parameters()
        
    def on_angle_changed(self, value):
        angle = float(value)
        self.angle_label.setText(f"Angle: {angle:.1f}°")
        self.update_canvas_parameters()
        
    def on_alpha_changed(self, value):
        alpha = value / 100.0
        self.alpha_label.setText(f"Alpha: {alpha:.2f}")
        self.update_canvas_parameters()
        
    def update_canvas_parameters(self):
        dx = self.dx_spin.value()
        dy = self.dy_spin.value()
        scale_x = self.scale_x_slider.value() / 100.0
        scale_y = self.scale_y_slider.value() / 100.0
        angle = self.angle_slider.value()
        alpha = self.alpha_slider.value() / 100.0
        
        self.image_canvas.set_parameters(dx, dy, scale_x, scale_y, angle, alpha)

    def set_parameter_controls(self, dx, dy, scale_x, scale_y, angle=None):
        controls = [
            self.dx_spin,
            self.dy_spin,
            self.scale_x_slider,
            self.scale_y_slider,
        ]

        if angle is not None:
            controls.append(self.angle_slider)

        for control in controls:
            control.blockSignals(True)

        self.dx_spin.setValue(int(dx))
        self.dy_spin.setValue(int(dy))
        self.scale_x_slider.setValue(int(round(scale_x * 100)))
        self.scale_y_slider.setValue(int(round(scale_y * 100)))
        if angle is not None:
            self.angle_slider.setValue(int(round(angle)))

        for control in controls:
            control.blockSignals(False)

        self.scale_x_label.setText(f"ScaleX: {scale_x:.2f}")
        self.scale_y_label.setText(f"ScaleY: {scale_y:.2f}")
        if angle is not None:
            self.angle_label.setText(f"Angle: {float(angle):.1f}°")

        self.update_canvas_parameters()
        
    def update_parameter_labels(self, dx=None, dy=None, scale_x=None, scale_y=None, angle=None):
        if dx is None or dy is None or scale_x is None or scale_y is None or angle is None:
            dx, dy, scale_x, scale_y, angle, alpha = self.image_canvas.get_parameters()
        self.set_parameter_controls(dx, dy, scale_x, scale_y, angle)

    def ensure_optimizer_available(self):
        try:
            from .optimizer import optimize_registration
        except ImportError:
            QMessageBox.critical(
                self,
                "缺少依赖",
                "自动优化依赖 SciPy。\n\n"
                "请执行：\n"
                "python -m pip install scipy==1.11.4",
            )
            return None

        return optimize_registration

    def auto_optimize_current_image(self):
        if self.image_canvas.ir_image is None or self.image_canvas.vis_image is None:
            QMessageBox.warning(self, "警告", "请先加载当前红外和可见光图像")
            return

        optimize_registration = self.ensure_optimizer_available()
        if optimize_registration is None:
            return

        initial_dx, initial_dy, initial_scale_x, initial_scale_y, angle, _ = self.image_canvas.get_parameters()

        progress = QProgressDialog("正在初始化自动优化...", None, 0, 0, self)
        progress.setWindowTitle("自动优化")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        QApplication.processEvents()

        def update_progress(label: str, iteration: int, evaluations: int) -> None:
            progress.setLabelText(f"{label}\n迭代次数: {iteration} | 目标函数评估: {evaluations}")
            QApplication.processEvents()

        try:
            result = optimize_registration(
                self.image_canvas.ir_image,
                self.image_canvas.vis_image,
                initial_dx=initial_dx,
                initial_dy=initial_dy,
                initial_scale_x=initial_scale_x,
                initial_scale_y=initial_scale_y,
                angle=angle,
                progress_callback=update_progress,
            )
        except Exception as exc:
            progress.close()
            QMessageBox.critical(self, "自动优化失败", f"自动优化过程中出现错误：\n{exc}")
            return

        progress.close()

        self.set_parameter_controls(
            result.dx,
            result.dy,
            result.scale_x,
            result.scale_y,
            result.angle,
        )
        self.save_parameters(show_message=False)

        self.info_label.setText(
            "自动优化完成: "
            f"dx={result.dx}, dy={result.dy}, "
            f"scale_x={result.scale_x:.3f}, scale_y={result.scale_y:.3f}, "
            f"score={result.score:.4f}"
        )
        QMessageBox.information(
            self,
            "自动优化完成",
            "已完成当前图像的自动优化并保存参数。\n\n"
            f"dx={result.dx}\n"
            f"dy={result.dy}\n"
            f"scale_x={result.scale_x:.4f}\n"
            f"scale_y={result.scale_y:.4f}\n"
            f"score={result.score:.4f}\n"
            f"success={result.success}\n"
            f"message={result.message}",
        )
        
    def save_parameters(self, show_message=True):
        if not self.ir_files:
            if show_message:
                QMessageBox.warning(self, "警告", "请先加载红外目录")
            return
        
        current_file = self.ir_files[self.current_index]
        dx, dy, scale_x, scale_y, angle, alpha = self.image_canvas.get_parameters()
        json_file = self.write_params_for_file(current_file, dx, dy, angle, scale_x, scale_y)
        
        if show_message:
            self.info_label.setText(f"已保存参数: dx={dx}, dy={dy}, angle={angle:.1f}°, scale_x={scale_x:.3f}, scale_y={scale_y:.3f}")
            QMessageBox.information(self, "保存成功", f"参数已保存到: {json_file}")

    def batch_auto_optimize(self):
        if not self.ir_files or not self.vis_files or self.ir_dir is None or self.vis_dir is None:
            QMessageBox.warning(self, "警告", "请先加载红外和可见光目录")
            return

        optimize_registration = self.ensure_optimizer_available()
        if optimize_registration is None:
            return

        reply = QMessageBox.question(
            self,
            "确认批量自动优化",
            "将对当前红外目录中的图像逐张执行自动优化，并把结果写入 results 目录。\n\n"
            "优化会优先使用已保存参数作为初始值；如果没有，则使用当前界面参数，"
            "并继续沿用上一张优化结果作为下一张的初始值。\n\n"
            f"共 {len(self.ir_files)} 张图像。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        current_file = self.ir_files[self.current_index] if self.ir_files else None
        current_dx, current_dy, current_scale_x, current_scale_y, current_angle, _ = self.image_canvas.get_parameters()
        carry_params = self.build_params_dict(
            current_dx,
            current_dy,
            current_angle,
            current_scale_x,
            current_scale_y,
        )

        progress = QProgressDialog("正在准备批量自动优化...", "取消", 0, len(self.ir_files), self)
        progress.setWindowTitle("批量自动优化")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        QApplication.processEvents()

        success_count = 0
        fail_count = 0
        skip_count = 0
        last_error = None

        for index, ir_file in enumerate(self.ir_files, start=1):
            if progress.wasCanceled():
                break

            vis_file = self.get_visible_file_for_ir(ir_file)
            if vis_file is None:
                skip_count += 1
                progress.setValue(index)
                continue

            ir_img = read_image(ir_file)
            vis_img = read_image(vis_file)
            if ir_img is None or vis_img is None:
                fail_count += 1
                progress.setValue(index)
                continue

            file_params = self.read_params_for_file(ir_file)
            init_params = file_params if file_params is not None else carry_params

            def update_progress(label: str, iteration: int, evaluations: int, *, name=ir_file.name, pos=index) -> None:
                progress.setLabelText(
                    f"[{pos}/{len(self.ir_files)}] {name}\n"
                    f"{label}\n"
                    f"迭代次数: {iteration} | 目标函数评估: {evaluations}"
                )
                QApplication.processEvents()

            try:
                result = optimize_registration(
                    ir_img,
                    vis_img,
                    initial_dx=init_params['dx'],
                    initial_dy=init_params['dy'],
                    initial_scale_x=init_params['scale_x'],
                    initial_scale_y=init_params['scale_y'],
                    angle=init_params['angle'],
                    progress_callback=update_progress,
                )
                self.write_params_for_file(
                    ir_file,
                    result.dx,
                    result.dy,
                    result.angle,
                    result.scale_x,
                    result.scale_y,
                )
                carry_params = self.build_params_dict(
                    result.dx,
                    result.dy,
                    result.angle,
                    result.scale_x,
                    result.scale_y,
                )
                success_count += 1
            except Exception as exc:
                fail_count += 1
                last_error = str(exc)

            progress.setValue(index)
            QApplication.processEvents()

        progress.close()

        if current_file in self.ir_files:
            self.current_index = self.ir_files.index(current_file)
            self.load_current_images()

        if progress.wasCanceled():
            self.info_label.setText(
                f"批量自动优化已取消：成功 {success_count} 张，失败 {fail_count} 张，跳过 {skip_count} 张"
            )
            QMessageBox.information(
                self,
                "批量自动优化已取消",
                f"成功: {success_count} 张\n失败: {fail_count} 张\n跳过: {skip_count} 张",
            )
            return

        self.info_label.setText(
            f"批量自动优化完成：成功 {success_count} 张，失败 {fail_count} 张，跳过 {skip_count} 张"
        )

        message = (
            f"成功: {success_count} 张\n"
            f"失败: {fail_count} 张\n"
            f"跳过: {skip_count} 张"
        )
        if last_error:
            message += f"\n\n最后一个错误:\n{last_error}"

        QMessageBox.information(self, "批量自动优化完成", message)
        
    def export_images(self):
        if not self.ir_files or not self.vis_files:
            QMessageBox.warning(self, "警告", "请先加载红外和可见光目录")
            return
        
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录", "")
        
        if not export_dir:
            return
        
        export_path = Path(export_dir)
        
        params_count = 0
        for ir_file in self.ir_files:
            json_file = self.result_dir / f"{ir_file.stem}.json"
            if json_file.exists():
                params_count += 1
        
        reply = QMessageBox.question(
            self, "确认导出",
            f"将使用 results 目录下的参数批量导出图像到:\n{export_path}\n\n"
            f"共 {len(self.ir_files)} 张图像\n"
            f"已配准: {params_count} 张\n"
            f"未配准: {len(self.ir_files) - params_count} 张\n\n"
            f"只导出已配准的图像",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        progress = QProgressBar()
        progress.setRange(0, len(self.ir_files))
        progress.setWindowTitle("导出进度")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.show()
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for i, ir_file in enumerate(self.ir_files):
            progress.setValue(i)
            QApplication.processEvents()
            
            json_file = self.result_dir / f"{ir_file.stem}.json"
            
            if not json_file.exists():
                skip_count += 1
                continue
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                    dx = params.get('dx', 0)
                    dy = params.get('dy', 0)
                    angle = params.get('angle', 0.0)
                    scale_x = params.get('scale_x', 1.0)
                    scale_y = params.get('scale_y', 1.0)
            except Exception as e:
                fail_count += 1
                continue
            
            rel_path = ir_file.relative_to(self.ir_dir)
            vis_file = self.vis_dir / rel_path
            
            if not vis_file.exists():
                fail_count += 1
                continue
            
            ir_img = read_image(ir_file)
            vis_img = read_image(vis_file)
            
            if ir_img is None or vis_img is None:
                fail_count += 1
                continue
            
            h, w = ir_img.shape[:2]
            
            if vis_img.shape[:2] != (h, w):
                vis_img = cv2.resize(vis_img, (w, h))
            
            center = (w // 2, h // 2)
            
            M_scale = cv2.getRotationMatrix2D(center, angle, 1.0)
            M_scale[0, 0] *= scale_x
            M_scale[1, 1] *= scale_y
            M_scale[0, 2] += dx
            M_scale[1, 2] += dy
            
            registered_img = cv2.warpAffine(ir_img, M_scale, (w, h))
            
            output_file = export_path / rel_path
            if write_image(output_file, registered_img):
                success_count += 1
            else:
                fail_count += 1
        
        progress.setValue(len(self.ir_files))
        progress.close()
        
        QMessageBox.information(self, "导出完成", 
            f"成功导出: {success_count} 张\n"
            f"跳过(未配准): {skip_count} 张\n"
            f"失败: {fail_count} 张\n"
            f"输出目录: {export_path}")
        
    def keyPressEvent(self, event):
        key = event.key()
        
        if self.use_global_mode:
            if key == Qt.Key.Key_Q or key == Qt.Key.Key_Escape:
                self.close()
            elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                self.alpha_slider.setValue(min(100, self.alpha_slider.value() + 10))
            elif key == Qt.Key.Key_Minus:
                self.alpha_slider.setValue(max(0, self.alpha_slider.value() - 10))
            elif key == Qt.Key.Key_S:
                self.save_parameters()
            return
        
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            if len(self.pressed_keys) == 1:
                self.key_repeat_timer.start(self.key_repeat_interval)
    
    def keyReleaseEvent(self, event):
        key = event.key()
        
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            
        if len(self.pressed_keys) == 0:
            self.key_repeat_timer.stop()
    
    def on_key_repeat(self):
        if self.use_global_mode:
            return
        
        for key in self.pressed_keys:
            if key == Qt.Key.Key_Left:
                self.dx_spin.setValue(self.dx_spin.value() - 1)
            elif key == Qt.Key.Key_Right:
                self.dx_spin.setValue(self.dx_spin.value() + 1)
            elif key == Qt.Key.Key_Up:
                self.dy_spin.setValue(self.dy_spin.value() - 1)
            elif key == Qt.Key.Key_Down:
                self.dy_spin.setValue(self.dy_spin.value() + 1)
            elif key == Qt.Key.Key_W:
                self.scale_x_slider.setValue(min(200, self.scale_x_slider.value() + 1))
            elif key == Qt.Key.Key_E:
                self.scale_x_slider.setValue(max(50, self.scale_x_slider.value() - 1))
            elif key == Qt.Key.Key_D:
                self.scale_y_slider.setValue(min(200, self.scale_y_slider.value() + 1))
            elif key == Qt.Key.Key_A:
                self.scale_y_slider.setValue(max(50, self.scale_y_slider.value() - 1))
            elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                self.alpha_slider.setValue(min(100, self.alpha_slider.value() + 10))
            elif key == Qt.Key.Key_Minus:
                self.alpha_slider.setValue(max(0, self.alpha_slider.value() - 10))
            elif key == Qt.Key.Key_S:
                self.save_parameters()
            elif key == Qt.Key.Key_Q or key == Qt.Key.Key_Escape:
                self.close()
    
    def simulate_key_press(self, key):
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            if len(self.pressed_keys) == 1:
                self.key_repeat_timer.start(self.key_repeat_interval)
    
    def simulate_key_release(self, key):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            
        if len(self.pressed_keys) == 0:
            self.key_repeat_timer.stop()


def main():
    app = QApplication(sys.argv)
    window = ImageRegistrationWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
