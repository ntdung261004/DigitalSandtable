# File: src/ui/editor_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFrame, QLabel, QPushButton, QFileDialog, 
                               QDialog, QLineEdit, QGraphicsView, QGraphicsScene)
from PySide6.QtGui import QPainter, QPixmap, QColor, QWheelEvent
from PySide6.QtCore import Qt
from src.utils import theme

class InfoDialog(QDialog):
    """
    Hộp thoại tùy chỉnh tăng kích thước ô nhập liệu để cập nhật Tên SA BÀN và Tỷ lệ
    """
    def __init__(self, current_name, current_scale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cập nhật thông tin hệ thống")
        self.setFixedSize(450, 260)
        self.setStyleSheet(f"background-color: #2c3e50; color: {theme.TITLE_COLOR}; font-family: '{theme.FONT_FAMILY}';")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Ô nhập tên SA BÀN
        layout.addWidget(QLabel("Tên SA BÀN:"))
        self.txt_name = QLineEdit(self)
        self.txt_name.setText(current_name)
        self.txt_name.setStyleSheet("background-color: #1e272e; color: white; padding: 10px; border-radius: 6px; border: 1px solid #718093; font-size: 15px;")
        self.txt_name.setFixedHeight(45) # Tăng kích thước chiều cao ô nhập liệu lớn hơn
        layout.addWidget(self.txt_name)
        
        # Ô nhập Tỷ lệ
        layout.addWidget(QLabel("Tỷ lệ sa bàn (Ví dụ: 1/2000):"))
        self.txt_scale = QLineEdit(self)
        self.txt_scale.setText(current_scale)
        self.txt_scale.setStyleSheet("background-color: #1e272e; color: white; padding: 10px; border-radius: 6px; border: 1px solid #718093; font-size: 15px;")
        self.txt_scale.setFixedHeight(45) # Tăng kích thước chiều cao ô nhập liệu lớn hơn
        layout.addWidget(self.txt_scale)
        
        # Các nút chức năng dưới cùng
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_ok = QPushButton("Xác nhận")
        self.btn_ok.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold; border-radius: 6px; border: none;")
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setStyleSheet("background-color: #c0392b; color: white; padding: 10px; font-weight: bold; border-radius: 6px; border: none;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
    def get_info(self):
        return self.txt_name.text().strip(), self.txt_scale.text().strip()


class InteractiveMapView(QGraphicsView):
    """
    Khung nhìn đồ họa bản đồ hỗ trợ di chuyển (Pan) và phóng to/thu nhỏ (Zoom) bằng chuột
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # Giữ chuột trái để kéo bản đồ

    def wheelEvent(self, event: QWheelEvent):
        # Lăn chuột để phóng to / thu nhỏ bản đồ
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)


class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bộ Biên Tập Sa Bàn Tác Chiến")
        
        self.sandtable_name = "Chưa đặt tên"
        self.sandtable_scale = "Chưa xác định"
        
        self.showMaximized()
        self.setStyleSheet(f"background-color: {theme.MAIN_BG_COLOR}; color: {theme.TITLE_COLOR}; font-family: '{theme.FONT_FAMILY}';")

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # =========================================================================
        # 1. THANH TÁC VỤ PHÍA TRÊN (TOP BAR)
        # =========================================================================
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        # Hiển thị thông tin SA BÀN viết hoa và trường Tỷ lệ mới
        self.lbl_scenario_title = QLabel(f"🗺️ SA BÀN: {self.sandtable_name}  |  Tỷ lệ: {self.sandtable_scale}")
        self.lbl_scenario_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #f1f2f6;")
        top_layout.addWidget(self.lbl_scenario_title)
        
        # Nút cập nhật thông tin hệ thống
        btn_rename = self.create_small_btn("📝 Cập nhật thông tin", "#2980b9")
        btn_rename.setFixedSize(160, 32)
        btn_rename.clicked.connect(self.update_sandtable_info)
        top_layout.addWidget(btn_rename)
        
        top_layout.addStretch() 
        
        btn_save = self.create_small_btn("💾 Lưu Sa Bàn", "#27ae60")
        btn_close = self.create_small_btn("🚪 Thoát Ra Menu", "#c0392b")
        btn_close.clicked.connect(self.close) 
        
        top_layout.addWidget(btn_save)
        top_layout.addWidget(btn_close)
        
        main_layout.addWidget(top_bar)

        # =========================================================================
        # 2. KHU VỰC TRUNG TÂM
        # =========================================================================
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(5)

        # --- A. CỘT TRÁI (LEFT SIDEBAR) ---
        left_sidebar = QFrame()
        left_sidebar.setFixedWidth(240)
        left_sidebar.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_left_title = QLabel("🛠️ THƯ VIỆN & CÔNG CỤ")
        lbl_left_title.setStyleSheet("font-weight: bold; border-bottom: 1px solid #7f8c8d; padding-bottom: 5px;")
        left_layout.addWidget(lbl_left_title)
        
        lbl_placeholder1 = QLabel("[Khu vực chứa các nút\nThêm Quân Ta / Địch\nvà Bút vẽ ranh giới]")
        lbl_placeholder1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_placeholder1.setStyleSheet("color: #bdc3c7; font-style: italic;")
        left_layout.addWidget(lbl_placeholder1)
        left_layout.addStretch()
        
        middle_layout.addWidget(left_sidebar)

        # --- B. KHUNG NHÌN CHÍNH (CENTER WORKSPACE) ---
        self.center_workspace = QFrame()
        self.center_workspace.setStyleSheet("background-color: #111111; border: 2px dashed #34495e; border-radius: 4px;")
        self.center_layout = QVBoxLayout(self.center_workspace)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Khởi tạo sẵn Sân khấu (Scene) đồ họa
        self.scene = QGraphicsScene()
        # Khởi tạo Khung nhìn đồ họa bản đồ chính
        self.view = InteractiveMapView(self.scene)
        self.view.hide() # Tạm thời ẩn đi cho đến khi chọn ảnh bản đồ
        self.center_layout.addWidget(self.view)
        
        # Văn bản thông báo ban đầu
        self.lbl_main_map_placeholder = QLabel("🗺️ KHÔNG GIAN HIỂN THỊ BẢN ĐỒ & SA BÀN CHÍNH\n(Vui lòng chọn hình ảnh bản đồ ở cột bên phải để bắt đầu)")
        self.lbl_main_map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main_map_placeholder.setStyleSheet("font-size: 16px; color: #7f8c8d; font-weight: bold;")
        self.center_layout.addWidget(self.lbl_main_map_placeholder)
        
        middle_layout.addWidget(self.center_workspace, stretch=1)

        # --- C. CỘT PHẢI (RIGHT PROPERTY PANEL) ---
        right_panel = QFrame()
        right_panel.setFixedWidth(240)
        right_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_right_title = QLabel("⚙️ TINH CHỈNH ĐỐI TƯỢNG")
        lbl_right_title.setStyleSheet("font-weight: bold; border-bottom: 1px solid #7f8c8d; padding-bottom: 5px;")
        right_layout.addWidget(lbl_right_title)

        # NÚT CHỌN BẢN ĐỒ (Đã đổi tên và cấu hình chức năng)
        btn_choose_map = QPushButton("📂 Chọn bản đồ")
        btn_choose_map.setFixedHeight(40)
        btn_choose_map.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                font-size: 14px; font-weight: bold; border-radius: 4px; border: none; margin-top: 10px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        btn_choose_map.clicked.connect(self.choose_map_file)
        right_layout.addWidget(btn_choose_map)
        
        self.lbl_map_path = QLabel("Chưa có bản đồ nào được chọn.")
        self.lbl_map_path.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 11px;")
        self.lbl_map_path.setWordWrap(True)
        right_layout.addWidget(self.lbl_map_path)
        
        lbl_placeholder2 = QLabel("\n\n[Hiển thị thông số:\n- Tên đơn vị\n- Tọa độ X, Y\n- Hướng/Góc xoay\nkhi click chọn icon]")
        lbl_placeholder2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_placeholder2.setStyleSheet("color: #bdc3c7; font-style: italic;")
        right_layout.addWidget(lbl_placeholder2)
        right_layout.addStretch()
        
        middle_layout.addWidget(right_panel)
        main_layout.addWidget(middle_widget, stretch=1)

        # =========================================================================
        # 3. THANH THỨ TỰ KỊCH BẢN PHÍA DƯỚI (BOTTOM TIMELINE PANEL)
        # =========================================================================
        bottom_panel = QFrame()
        bottom_panel.setFixedHeight(140) 
        bottom_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_bottom_title = QLabel("⏳ TIẾN TRÌNH TÁC CHIẾN (TIMELINE)")
        lbl_bottom_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #f1f2f6;")
        bottom_layout.addWidget(lbl_bottom_title)
        
        lbl_placeholder3 = QLabel("[Thanh tiến trình quản lý các pha hành động tác chiến theo thứ tự thời gian]")
        lbl_placeholder3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_placeholder3.setStyleSheet("color: #bdc3c7; font-style: italic;")
        bottom_layout.addWidget(lbl_placeholder3)
        bottom_layout.addStretch()

        main_layout.addWidget(bottom_panel)
        self.setCentralWidget(main_widget)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN NÚT BẤM ---

    def update_sandtable_info(self):
        """Mở hộp thoại mở rộng để cập nhật đồng thời Tên SA BÀN và Tỷ lệ"""
        dialog = InfoDialog(self.sandtable_name, self.sandtable_scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, scale = dialog.get_info()
            if name:
                self.sandtable_name = name
            if scale:
                self.sandtable_scale = scale
            
            # Cập nhật thông tin chuỗi hiển thị lên thanh công cụ
            self.lbl_scenario_title.setText(f"🗺️ SA BÀN: {self.sandtable_name}  |  Tỷ lệ: {self.sandtable_scale}")

    def choose_map_file(self):
        """Mở hộp thoại tải tệp ảnh bản đồ và hiển thị trực tiếp lên vùng trung tâm"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Chọn file ảnh bản đồ nền sa bàn", 
            "", 
            "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_path and os.path.exists(file_path):
            # Hiển thị tên tệp ở thanh bên phải
            self.lbl_map_path.setText(f"File: {os.path.basename(file_path)}")
            
            # Đọc hình ảnh và đẩy vào Sân khấu (Scene) đồ họa
            pixmap = QPixmap(file_path)
            self.scene.clear() # Dọn dẹp tài nguyên cũ nếu có
            self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(pixmap.rect())
            
            # Ẩn văn bản hướng dẫn và hiển thị Khung nhìn bản đồ
            self.lbl_main_map_placeholder.hide()
            self.view.show()
            
            # Căn chỉnh kích thước bản đồ vừa vặn với vùng hiển thị ban đầu
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def create_small_btn(self, text, bg_color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color}; color: white;
                font-size: 13px; font-weight: bold; border-radius: 4px; border: none;
            }}
            QPushButton:hover {{ background-color: #34495e; border: 1px solid #7f8c8d; }}
        """)
        return btn