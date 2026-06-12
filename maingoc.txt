import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QGraphicsView, 
                               QGraphicsScene, QVBoxLayout, QHBoxLayout, QWidget, 
                               QPushButton, QGraphicsPixmapItem)
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent
from PySide6.QtCore import Qt

class DraggableSymbol(QGraphicsPixmapItem):
    def __init__(self, pixmap_path, target_size=28):
        # 1. Tải và thu nhỏ ảnh gốc
        original_pixmap = QPixmap(pixmap_path)
        scaled_pixmap = original_pixmap.scaled(
            target_size, target_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(scaled_pixmap)
        
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable)
        self.setTransformOriginPoint(self.boundingRect().center())

    def mousePressEvent(self, event):
        # 2. Xử lý khi nhấn chuột vào ký hiệu
        if event.button() == Qt.MouseButton.RightButton:
            # Nếu giữ thêm phím Shift + Click chuột phải: Xoay ngược chiều kim đồng hồ
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.setRotation(self.rotation() - 15)
            # Nếu chỉ Click chuột phải: Xoay cùng chiều kim đồng hồ
            else:
                self.setRotation(self.rotation() + 15)
            event.accept()
        else:
            # 3. Rất quan trọng: Nếu không phải chuột phải (VD: chuột trái), 
            # phải trả lại sự kiện cho lớp cha để nó xử lý tính năng Kéo Thả.
            super().mousePressEvent(event)

class InteractiveMapView(QGraphicsView):
    def __init__(self, scene, is_control_panel=False, sync_view=None):
        super().__init__(scene)
        # Đã sửa lỗi RenderHint ở đây, sử dụng QPainter thay vì Qt
        self.setRenderHint(QPainter.RenderHint.Antialiasing) 
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

        self.is_control_panel = is_control_panel
        self.sync_view = sync_view

        if self.is_control_panel:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def wheelEvent(self, event: QWheelEvent):
        if not self.is_control_panel:
            return 
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)
        if self.sync_view:
            self.sync_view.setTransform(self.transform())

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        if self.is_control_panel and self.sync_view:
            self.sync_view.horizontalScrollBar().setValue(self.horizontalScrollBar().value())
            self.sync_view.verticalScrollBar().setValue(self.verticalScrollBar().value())

class DisplayWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("Sa bàn - Trình chiếu")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #000000;")
        self.view = InteractiveMapView(scene, is_control_panel=False)
        self.setCentralWidget(self.view)

class ControlPanelWindow(QMainWindow):
    def __init__(self, scene, display_view):
        super().__init__()
        self.scene = scene
        self.setWindowTitle("Bảng Điều Khiển Tác Chiến")
        self.resize(1000, 600)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TẠO SIDEBAR ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(220)
        sidebar_widget.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- NHÓM QUÂN TA (Màu Xanh) ---
        lbl_ta = QLabel("🟦 QUÂN TA")
        lbl_ta.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0 5px 0;")
        sidebar_layout.addWidget(lbl_ta)

        sidebar_layout.addWidget(self.create_spawn_btn("ta", "xetang", "Xe Tăng"))
        sidebar_layout.addWidget(self.create_spawn_btn("ta", "bobinh", "Bộ Binh"))
        sidebar_layout.addWidget(self.create_spawn_btn("ta", "phaobinh", "Pháo Binh"))
        sidebar_layout.addWidget(self.create_spawn_btn("ta", "cancu", "Căn Cứ"))

        # --- NHÓM QUÂN ĐỊCH (Màu Đỏ) ---
        lbl_dich = QLabel("🟥 QUÂN ĐỊCH")
        lbl_dich.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px 0 5px 0;")
        sidebar_layout.addWidget(lbl_dich)

        sidebar_layout.addWidget(self.create_spawn_btn("dich", "xetang", "Xe Tăng"))
        sidebar_layout.addWidget(self.create_spawn_btn("dich", "bobinh", "Bộ Binh"))
        sidebar_layout.addWidget(self.create_spawn_btn("dich", "phaobinh", "Pháo Binh"))
        sidebar_layout.addWidget(self.create_spawn_btn("dich", "cancu", "Căn Cứ"))

        # --- PHẦN BẢN ĐỒ ---
        self.view = InteractiveMapView(scene, is_control_panel=True, sync_view=display_view)

        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.view)
        self.setCentralWidget(central_widget)

    def create_spawn_btn(self, faction, unit, label):
        """Hàm hỗ trợ tạo nút bấm nhanh gọn, tự phân màu theo Phe"""
        btn = QPushButton(f"+ Thêm {label}")
        bg_color = "#2980b9" if faction == "ta" else "#c0392b"
        btn.setStyleSheet(f"background-color: {bg_color}; padding: 8px; font-size: 14px; margin-bottom: 5px; border-radius: 4px; border: none;")
        # Sử dụng lambda để truyền tham số Phe và Loại đơn vị vào hàm xử lý
        btn.clicked.connect(lambda: self.spawn_symbol(faction, unit))
        return btn

    def spawn_symbol(self, faction, unit):
        """Hàm sinh ra ký hiệu dựa trên Phe (ta/dich) và Loại đơn vị (xetang/bobinh...)"""
        # Cập nhật đường dẫn theo cấu trúc thư mục: assets/KyHieu/ta/xetang.png
        symbol_path = os.path.join("assets", "KyHieu", faction, f"{unit}.png")
        
        if os.path.exists(symbol_path):
            item = DraggableSymbol(symbol_path)
            center_point = self.view.mapToScene(self.view.viewport().rect().center())
            item.setPos(center_point.x() - item.boundingRect().width()/2, 
                        center_point.y() - item.boundingRect().height()/2)
            self.scene.addItem(item)
        else:
            print(f"Lỗi: Không tìm thấy file {symbol_path}")

def main():
    app = QApplication(sys.argv)

    scene = QGraphicsScene()
    
    # Cập nhật đường dẫn load bản đồ: assets/Bandomau/bando1.jpeg
    map_path = os.path.join("assets", "Bandomau", "bando1.jpeg") 
    
    if os.path.exists(map_path):
        pixmap = QPixmap(map_path)
        scene.addPixmap(pixmap)
        scene.setSceneRect(pixmap.rect())
    else:
        print(f"Lỗi: Không tìm thấy file bản đồ tại {map_path}")

    display_win = DisplayWindow(scene)
    control_win = ControlPanelWindow(scene, display_win.view)

    screens = app.screens()
    if len(screens) > 1:
        second_screen = screens[1]
        display_win.move(second_screen.geometry().topLeft())
        display_win.showFullScreen()
    else:
        display_win.resize(640, 480)
        display_win.setWindowTitle("Màn hình máy chiếu (Test)")
        display_win.show()

    control_win.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()