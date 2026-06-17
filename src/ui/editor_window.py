# File: src/ui/editor_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFrame, QLabel, QPushButton, QFileDialog, 
                               QDialog, QLineEdit, QGraphicsView, QGraphicsScene, 
                               QMessageBox, QApplication, QStackedWidget, QButtonGroup,
                               QScrollArea)
from PySide6.QtGui import QPainter, QPixmap, QColor, QWheelEvent, QPen
from PySide6.QtCore import Qt, QRectF
from src.utils import theme

class InfoDialog(QDialog):
    def __init__(self, current_name, current_scale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cập nhật thông tin hệ thống")
        self.setFixedSize(450, 260)
        self.setStyleSheet(f"background-color: #2c3e50; color: {theme.TITLE_COLOR}; font-family: '{theme.FONT_FAMILY}';")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel("Tên SA BÀN:"))
        self.txt_name = QLineEdit(self)
        self.txt_name.setText(current_name)
        self.txt_name.setStyleSheet("background-color: #1e272e; color: white; padding: 10px; border-radius: 6px; border: 1px solid #718093; font-size: 15px;")
        self.txt_name.setFixedHeight(45) 
        layout.addWidget(self.txt_name)
        
        layout.addWidget(QLabel("Tỷ lệ sa bàn (Ví dụ: 1/2000):"))
        self.txt_scale = QLineEdit(self)
        self.txt_scale.setText(current_scale)
        self.txt_scale.setStyleSheet("background-color: #1e272e; color: white; padding: 10px; border-radius: 6px; border: 1px solid #718093; font-size: 15px;")
        self.txt_scale.setFixedHeight(45) 
        layout.addWidget(self.txt_scale)
        
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


class DisplayWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("Sa bàn - Trình chiếu")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #000000;")
        self.view = InteractiveMapView(scene, is_projector=True)
        self.setCentralWidget(self.view)


class InteractiveMapView(QGraphicsView):
    def __init__(self, scene, main_window=None, is_projector=False, parent=None):
        super().__init__(scene, parent)
        self.main_window = main_window 
        self.is_projector = is_projector
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) 
        
        self.grid_size = 100 
        self.show_grid = False
        self.select_region_mode = False
        self.selection_start_pos = None

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if self.select_region_mode and event.button() == Qt.MouseButton.LeftButton:
            self.selection_start_pos = self.mapToScene(event.pos())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.select_region_mode and event.button() == Qt.MouseButton.LeftButton and self.selection_start_pos:
            selection_end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.selection_start_pos, selection_end_pos).normalized()
            
            if rect.width() > 50 and rect.height() > 50:
                if self.main_window:
                    self.main_window.set_projection_region(rect)
            self.selection_start_pos = None

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        
        if not self.show_grid or not self.scene() or self.grid_size <= 0:
            return

        scene_rect = self.scene().sceneRect()
        left = int(scene_rect.left())
        right = int(scene_rect.right())
        top = int(scene_rect.top())
        bottom = int(scene_rect.bottom())

        pen = QPen(QColor(0, 255, 255, 120))
        pen.setWidth(1)
        pen.setCosmetic(True) 
        painter.setPen(pen)

        for x in range(left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)

        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(0, 255, 255, 220))

        col = 1
        for x in range(left, right, self.grid_size):
            row = 1
            for y in range(top, bottom, self.grid_size):
                letter = chr(64 + min(row, 26)) if row <= 26 else str(row)
                label = f"{letter}-{col:02d}"
                painter.drawText(x + 5, y + 20, label)
                row += 1
            col += 1


class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bộ Biên Tập Sa Bàn Tác Chiến")
        
        self.sandtable_name = "Chưa đặt tên"
        self.sandtable_scale = "Chưa xác định"
        self.current_pixmap = None 
        self.projection_rect = None 
        self.projection_frame_item = None 
        
        self.showMaximized()
        self.setStyleSheet(f"background-color: {theme.MAIN_BG_COLOR}; color: {theme.TITLE_COLOR}; font-family: '{theme.FONT_FAMILY}';")

        self.scene = QGraphicsScene()
        self.display_win = DisplayWindow(self.scene)
        
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.display_win.move(second_screen.geometry().topLeft())
            self.display_win.showFullScreen()
        else:
            self.display_win.resize(800, 600)
            self.display_win.show()

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # =========================================================================
        # 1. THANH TÁC VỤ PHÍA TRÊN
        # =========================================================================
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_scenario_title = QLabel(f"🗺️ SA BÀN: {self.sandtable_name}  |  Tỷ lệ: {self.sandtable_scale}")
        self.lbl_scenario_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #f1f2f6;")
        top_layout.addWidget(self.lbl_scenario_title)
        
        btn_rename = self.create_small_btn("📝 Cập nhật thông tin", "#2980b9")
        btn_rename.setFixedSize(160, 32)
        btn_rename.clicked.connect(self.update_sandtable_info)
        top_layout.addWidget(btn_rename)
        
        top_layout.addStretch() 
        
        btn_save = self.create_small_btn("💾 Lưu Sa Bàn", "#27ae60")
        btn_close = self.create_small_btn("🚪 Thoát Ra Menu", "#c0392b")
        btn_close.clicked.connect(self.close_all) 
        
        top_layout.addWidget(btn_save)
        top_layout.addWidget(btn_close)
        
        main_layout.addWidget(top_bar)

        # =========================================================================
        # 2. KHU VỰC TRUNG TÂM (UI CANVA STYLE - 3 LỚP)
        # =========================================================================
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        # --- LỚP 1: THANH MENU GỐC (FAR-LEFT BAR) ---
        far_left_bar = QFrame()
        far_left_bar.setFixedWidth(75)
        far_left_bar.setStyleSheet("background-color: #1a2228; border-top-left-radius: 4px; border-bottom-left-radius: 4px;")
        far_left_layout = QVBoxLayout(far_left_bar)
        far_left_layout.setContentsMargins(5, 15, 5, 15)
        far_left_layout.setSpacing(15)

        self.main_tab_group = QButtonGroup(self)
        
        tab_btn_css = """
            QPushButton { background-color: transparent; color: #bdc3c7; font-weight: bold; border-radius: 8px; padding: 10px 0px; font-size: 11px;}
            QPushButton:hover { background-color: #2c3e50; color: white; }
            QPushButton:checked { background-color: #2c3e50; color: #e67e22; }
        """

        self.btn_tab_map = QPushButton("🗺️\nBản đồ")
        self.btn_tab_map.setCheckable(True)
        self.btn_tab_map.setChecked(True)
        self.btn_tab_map.setStyleSheet(tab_btn_css)
        self.main_tab_group.addButton(self.btn_tab_map, 0)
        far_left_layout.addWidget(self.btn_tab_map)

        self.btn_tab_tools = QPushButton("🛠️\nCông cụ")
        self.btn_tab_tools.setCheckable(True)
        self.btn_tab_tools.setStyleSheet(tab_btn_css)
        self.main_tab_group.addButton(self.btn_tab_tools, 1)
        far_left_layout.addWidget(self.btn_tab_tools)

        far_left_layout.addStretch()
        middle_layout.addWidget(far_left_bar)

        # --- LỚP 2: BẢNG DANH MỤC (SUB-PANEL BẰNG QStackedWidget) ---
        self.sub_panel = QStackedWidget()
        self.sub_panel.setFixedWidth(160)
        self.sub_panel.setStyleSheet("background-color: #2c3e50; border-top-right-radius: 4px; border-bottom-right-radius: 4px;")
        
        self.main_tab_group.idClicked.connect(self.sub_panel.setCurrentIndex)

        # [Trang 1 của Lớp 2]: Bản Đồ & Tọa Độ
        page_map = QWidget()
        page_map_layout = QVBoxLayout(page_map)
        page_map_layout.setContentsMargins(10, 15, 10, 15)
        page_map_layout.setSpacing(10)

        btn_choose_map = QPushButton("📂 Tải bản đồ")
        btn_choose_map.setFixedHeight(35)
        btn_choose_map.setStyleSheet("QPushButton { background-color: #e67e22; color: white; font-weight: bold; border-radius: 4px; border: none; } QPushButton:hover { background-color: #d35400; }")
        btn_choose_map.clicked.connect(self.choose_map_file)
        page_map_layout.addWidget(btn_choose_map)
        
        self.lbl_map_path = QLabel("Chưa có bản đồ.")
        self.lbl_map_path.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 11px;")
        self.lbl_map_path.setWordWrap(True)
        page_map_layout.addWidget(self.lbl_map_path)

        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setStyleSheet("color: #7f8c8d; margin: 5px 0;")
        page_map_layout.addWidget(line1)

        self.btn_grid = QPushButton("🌐 Bật Lưới")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setStyleSheet("QPushButton { background-color: #1e272e; color: white; padding: 10px; font-weight: bold; border-radius: 4px; border: none; } QPushButton:checked { background-color: #0984e3; }")
        self.btn_grid.clicked.connect(self.toggle_grid)
        page_map_layout.addWidget(self.btn_grid)

        self.btn_region = QPushButton("🎯 Chọn Vùng")
        self.btn_region.setCheckable(True)
        self.btn_region.setStyleSheet("QPushButton { background-color: #1e272e; color: white; padding: 10px; font-weight: bold; border-radius: 4px; border: none; } QPushButton:checked { background-color: #c0392b; }")
        self.btn_region.clicked.connect(self.toggle_region_select)
        page_map_layout.addWidget(self.btn_region)
        
        page_map_layout.addStretch()
        self.sub_panel.addWidget(page_map)

        # [Trang 2 của Lớp 2]: Công Cụ Thiết Kế
        page_tools = QWidget()
        page_tools_layout = QVBoxLayout(page_tools)
        page_tools_layout.setContentsMargins(10, 15, 10, 15)
        page_tools_layout.setSpacing(8)

        self.tool_category_group = QButtonGroup(self)
        self.tool_category_group.idClicked.connect(self.on_tool_category_changed)

        tools_list = [
            (0, "🖱️  Con trỏ"),
            (1, "🖌️  Vẽ tự do"),
            (2, "⬛  Hình học"),
            (3, "➖  Đường kẻ"),
            (4, "🇹  Văn bản")
        ]

        tool_btn_css = """
            QPushButton { 
                background-color: transparent; color: #f5f6fa; font-weight: bold; font-size: 13px;
                text-align: left; padding: 10px 5px; border-radius: 6px; border: 1px solid transparent;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:checked { background-color: #e67e22; color: #111111; }
        """

        for t_id, t_label in tools_list:
            btn = QPushButton(t_label)
            btn.setCheckable(True)
            btn.setStyleSheet(tool_btn_css)
            self.tool_category_group.addButton(btn, t_id)
            page_tools_layout.addWidget(btn)
            if t_id == 0: btn.setChecked(True)

        page_tools_layout.addStretch()
        self.sub_panel.addWidget(page_tools)

        middle_layout.addWidget(self.sub_panel)
        middle_layout.addSpacing(5) 

        # --- B. KHUNG NHÌN CHÍNH (CENTER WORKSPACE) ---
        self.center_workspace = QFrame()
        # 1. ĐÃ XÓA nét đứt (dashed) ở viền khung hiển thị chính, thay bằng border: none
        self.center_workspace.setStyleSheet("background-color: #111111; border: none; border-radius: 4px;")
        self.center_layout = QVBoxLayout(self.center_workspace)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.view = InteractiveMapView(self.scene, main_window=self)
        self.view.hide() 
        self.center_layout.addWidget(self.view)
        
        self.lbl_main_map_placeholder = QLabel("🗺️ KHÔNG GIAN HIỂN THỊ BẢN ĐỒ & SA BÀN CHÍNH\n(Mở ngăn 'Bản đồ' ở cột trái để tải ảnh lên)")
        self.lbl_main_map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main_map_placeholder.setStyleSheet("font-size: 16px; color: #7f8c8d; font-weight: bold;")
        self.center_layout.addWidget(self.lbl_main_map_placeholder)

        # --- LỚP 3: BẢNG NỔI CHỨA HÌNH HỌC (FLOATING OVERLAY) ---
        self.floating_panel = QFrame(self.center_workspace)
        self.floating_panel.setFixedWidth(60)
        self.floating_panel.setFixedHeight(300)
        self.floating_panel.setStyleSheet("""
            QFrame {
                background-color: #2c3e50; 
                border-radius: 8px; 
                border: 1px solid #1a2228;
            }
        """)
        
        float_layout = QVBoxLayout(self.floating_panel)
        float_layout.setContentsMargins(0, 5, 0, 5)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QScrollBar:vertical { width: 0px; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_content_layout = QVBoxLayout(scroll_content)
        scroll_content_layout.setContentsMargins(10, 5, 10, 5)
        scroll_content_layout.setSpacing(10)
        
        shapes = [
            ("□", "rect"), ("○", "ellipse"), ("△", "triangle"), 
            ("◇", "diamond"), ("⬠", "pentagon"), ("⬡", "hexagon"), 
            ("☆", "star")
        ]
        
        for icon, s_id in shapes:
            btn = QPushButton(icon)
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: white; font-size: 22px; border-radius: 4px; } 
                QPushButton:hover { background-color: #34495e; } 
                QPushButton:pressed { background-color: #e67e22; color: #111111; }
            """)
            scroll_content_layout.addWidget(btn)
            
        scroll_content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        float_layout.addWidget(scroll_area)
        
        self.floating_panel.move(10, 10) 
        self.floating_panel.hide() 
        
        middle_layout.addWidget(self.center_workspace, stretch=1)

        # --- C. CỘT PHẢI (THUỘC TÍNH CHI TIẾT ĐỘNG) ---
        right_panel = QFrame()
        right_panel.setFixedWidth(240)
        right_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_right_title = QLabel("⚙️ THUỘC TÍNH ĐỐI TƯỢNG")
        lbl_right_title.setStyleSheet("font-weight: bold; border-bottom: 1px solid #7f8c8d; padding-bottom: 10px; color: #f1c40f;")
        right_layout.addWidget(lbl_right_title)

        lbl_properties_hint = QLabel("\n\n\n\n\nChưa có đối tượng nào được chọn.\n\n(Bảng này sẽ hiện thông số khi bạn bấm chọn một hình vẽ hoặc xe tăng)")
        lbl_properties_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_properties_hint.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 12px;")
        lbl_properties_hint.setWordWrap(True)
        right_layout.addWidget(lbl_properties_hint)
        
        right_layout.addStretch()
        
        middle_layout.addWidget(right_panel)
        main_layout.addWidget(middle_widget, stretch=1)

        # =========================================================================
        # 3. THANH THỨ TỰ KỊCH BẢN PHÍA DƯỚI
        # =========================================================================
        bottom_panel = QFrame()
        bottom_panel.setFixedHeight(140) 
        bottom_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_bottom_title = QLabel("⏳ TIẾN TRÌNH TÁC CHIẾN (TIMELINE)")
        lbl_bottom_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #f1f2f6;")
        bottom_layout.addWidget(lbl_bottom_title)
        bottom_layout.addStretch()

        main_layout.addWidget(bottom_panel)
        self.setCentralWidget(main_widget)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN GIAO DIỆN ---
    def on_tool_category_changed(self, tool_id):
        if tool_id == 2: 
            self.floating_panel.show()
            self.floating_panel.raise_() 
        else:
            self.floating_panel.hide()

    # --- CÁC HÀM XỬ LÝ LƯỚI VÀ CHỌN VÙNG TRÌNH CHIẾU ---
    def toggle_grid(self, checked):
        self.view.show_grid = checked
        self.display_win.view.show_grid = checked
        self.btn_grid.setText("🌐 Tắt Lưới Tọa Độ" if checked else "🌐 Bật Lưới Tọa Độ")
        self.scene.update() 

    def toggle_region_select(self, checked):
        self.view.select_region_mode = checked
        if checked:
            self.btn_region.setText("🎯 Hủy Chọn")
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            QMessageBox.information(self, "Hướng dẫn", "Hãy dùng chuột TRÁI, nhấn giữ và kéo một vùng hình chữ nhật để thiết lập khu vực sẽ chiếu lên màn hình lớn.")
        else:
            self.btn_region.setText("🎯 Chọn Vùng Trình Chiếu")
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def set_projection_region(self, rect):
        if not self.current_pixmap: return
        reply = QMessageBox.question(self, 'Xác nhận Vùng Trình Chiếu', 
                                     'Thiết lập đây là khu vực duy nhất sẽ hiển thị trên máy chiếu (Các phần viền đen sẽ bị ẩn)?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.projection_rect = rect.toRect().intersected(self.current_pixmap.rect())
            if self.projection_frame_item in self.scene.items():
                self.scene.removeItem(self.projection_frame_item)
            
            from PySide6.QtWidgets import QGraphicsRectItem
            self.projection_frame_item = QGraphicsRectItem(self.projection_rect)
            pen = QPen(QColor(230, 126, 34)) 
            pen.setWidth(4)
            # 2. ĐÃ ĐỔI: Thay Qt.PenStyle.DashLine thành SolidLine cho khung chọn hiển thị
            pen.setStyle(Qt.PenStyle.SolidLine) 
            self.projection_frame_item.setPen(pen)
            self.projection_frame_item.setZValue(9999) 
            self.scene.addItem(self.projection_frame_item)
            
            self.display_win.view.fitInView(self.projection_rect, Qt.AspectRatioMode.KeepAspectRatio)
            
        self.btn_region.setChecked(False)
        self.toggle_region_select(False)

    def update_sandtable_info(self):
        dialog = InfoDialog(self.sandtable_name, self.sandtable_scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, scale = dialog.get_info()
            if name: self.sandtable_name = name
            if scale: self.sandtable_scale = scale
            self.lbl_scenario_title.setText(f"🗺️ SA BÀN: {self.sandtable_name}  |  Tỷ lệ: {self.sandtable_scale}")

    def choose_map_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file ảnh bản đồ", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path and os.path.exists(file_path):
            self.lbl_map_path.setText(f"File: {os.path.basename(file_path)}")
            self.current_pixmap = QPixmap(file_path)
            self.scene.clear() 
            self.scene.addPixmap(self.current_pixmap)
            self.scene.setSceneRect(self.current_pixmap.rect())
            self.projection_rect = None
            self.projection_frame_item = None
            self.lbl_main_map_placeholder.hide()
            self.view.show()
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def close_all(self):
        self.display_win.close()
        self.close()

    def create_small_btn(self, text, bg_color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_color}; color: white; font-size: 13px; font-weight: bold; border-radius: 4px; border: none; }}
            QPushButton:hover {{ background-color: #34495e; border: 1px solid #7f8c8d; }}
        """)
        return btn