# File: src/ui/main_menu.py
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QPushButton, QLabel, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QPainter, QPixmap, QColor
from PySide6.QtCore import Qt

# Import file cấu hình theme
from src.utils import theme
# Import file màn hình editor
from src.ui.editor_window import EditorWindow

class MainMenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ Thống Sa Bàn Tác Chiến Điện Tử")
        
        # Tạo widget trung tâm trong suốt để lộ hình nền phía dưới
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- TIÊU ĐỀ ---
        title_label = QLabel("HỆ THỐNG SA BÀN TÁC CHIẾN ĐIỆN TỬ")
        title_label.setStyleSheet(f"""
            color: {theme.TITLE_COLOR}; 
            font-family: '{theme.FONT_FAMILY}';
            font-size: {theme.TITLE_FONT_SIZE}; 
            font-weight: {theme.TITLE_FONT_WEIGHT}; 
            margin-bottom: 50px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- CÁC NÚT CHỨC NĂNG ---
        self.btn_new = self.create_button("🎯 TẠO SA BÀN MỚI")
        self.btn_load = self.create_button("📂 MỞ SA BÀN ĐÃ LƯU")
        self.btn_assets = self.create_button("⚙️ QUẢN LÝ DỮ LIỆU")
        self.btn_settings = self.create_button("🛠 CÀI ĐẶT HỆ THỐNG")
        self.btn_exit = self.create_button("🚪 THOÁT HỆ THỐNG")

        # Gắn sự kiện các nút
        self.btn_new.clicked.connect(self.open_editor)
        self.btn_exit.clicked.connect(self.close)

        layout.addWidget(self.btn_new, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_load, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_assets, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignCenter)
        
        spacer = QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        layout.addSpacerItem(spacer)
        layout.addWidget(self.btn_exit, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(central_widget)

        # --- TẢI ẢNH NỀN VÀO BỘ NHỚ ---
        self.bg_pixmap = None
        if os.path.exists(theme.BG_IMAGE_PATH):
            self.bg_pixmap = QPixmap(theme.BG_IMAGE_PATH)

    def paintEvent(self, event):
        """Hàm này tự động chạy để vẽ nền mỗi khi cửa sổ thay đổi kích thước"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Vẽ màu nền chủ đạo (Màu tối)
        rect = self.rect()
        painter.fillRect(rect, QColor(theme.MAIN_BG_COLOR))

        # 2. Phủ ảnh nền chìm lên trên
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            # Thiết lập độ mờ cho nét cọ
            painter.setOpacity(theme.BG_IMAGE_OPACITY)
            
            # Cắt/phóng to ảnh sao cho phủ kín màn hình mượt mà
            scaled_pixmap = self.bg_pixmap.scaled(
                rect.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Căn giữa ảnh nền
            x = (rect.width() - scaled_pixmap.width()) // 2
            y = (rect.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
        
        painter.end()

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(theme.BTN_WIDTH, theme.BTN_HEIGHT)
        
        # Chèn các biến theme vào file CSS của nút
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BTN_BG_COLOR};
                color: {theme.BTN_TEXT_COLOR};
                font-family: '{theme.FONT_FAMILY}';
                font-size: {theme.BTN_FONT_SIZE};
                font-weight: {theme.BTN_FONT_WEIGHT};
                border-radius: {theme.BTN_BORDER_RADIUS};
                border: 2px solid {theme.BTN_BORDER_COLOR};
            }}
            QPushButton:hover {{
                background-color: {theme.BTN_HOVER_BG_COLOR};
                border: 2px solid {theme.BTN_HOVER_BORDER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {theme.BTN_PRESSED_BG_COLOR};
            }}
        """)
        return btn

    def open_editor(self):
        # Khởi tạo màn hình biên tập sa bàn số hóa
        self.editor_win = EditorWindow()
        self.editor_win.show()
        # Ẩn tạm màn hình Menu chính đi
        self.close()