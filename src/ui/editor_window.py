# File: src/ui/editor_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFrame, QLabel, QPushButton, QFileDialog, 
                               QMessageBox, QApplication, QStackedWidget, QButtonGroup,
                               QScrollArea, QGridLayout, QSpinBox, QGraphicsScene,
                               QGraphicsView, QGraphicsItem, QCheckBox, QGraphicsDropShadowEffect, QLineEdit)
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF

from src.utils import theme
from src.ui.components.dialogs import InfoDialog
from src.ui.components.projector import DisplayWindow
from src.ui.components.canvas import InteractiveMapView, DraggableShape

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
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        self.display_win = DisplayWindow(self.scene)
        
        screens = QApplication.screens()
        if len(screens) > 1:
            second_screen = screens[1]
            self.display_win.move(second_screen.geometry().topLeft())
            self.display_win.showFullScreen()
        else:
            self.display_win.resize(800, 600)
            self.display_win.show()

        self.setup_ui()
        self.setup_quick_action_bar()

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # === THANH TRÊN ===
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

        # === KHU VỰC TRUNG TÂM ===
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        # --- LỚP 1: MENU GỐC ---
        far_left_bar = QFrame()
        far_left_bar.setFixedWidth(75)
        far_left_bar.setStyleSheet("background-color: #1a2228; border-top-left-radius: 4px; border-bottom-left-radius: 4px;")
        far_left_layout = QVBoxLayout(far_left_bar)
        far_left_layout.setContentsMargins(5, 15, 5, 15)
        far_left_layout.setSpacing(15)

        self.main_tab_group = QButtonGroup(self)
        tab_btn_css = "QPushButton { background-color: transparent; color: #bdc3c7; font-weight: bold; border-radius: 8px; padding: 10px 0px; font-size: 11px;} QPushButton:hover { background-color: #2c3e50; color: white; } QPushButton:checked { background-color: #2c3e50; color: #e67e22; }"

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

        # --- LỚP 2: BẢNG DANH MỤC ---
        self.sub_panel = QStackedWidget()
        self.sub_panel.setFixedWidth(160)
        self.sub_panel.setStyleSheet("background-color: #2c3e50; border-top-right-radius: 4px; border-bottom-right-radius: 4px;")
        self.main_tab_group.idClicked.connect(self.sub_panel.setCurrentIndex)

        page_map = QWidget()
        page_map_layout = QVBoxLayout(page_map)
        page_map_layout.setContentsMargins(10, 15, 10, 15)
        page_map_layout.setSpacing(10)
        btn_choose_map = QPushButton("📂 Tải bản đồ")
        btn_choose_map.setFixedHeight(35)
        btn_choose_map.setStyleSheet("QPushButton { background-color: #e67e22; color: white; font-weight: bold; border-radius: 4px; border: none; } QPushButton:hover { background-color: #d35400; }")
        btn_choose_map.clicked.connect(self.choose_map_file)
        page_map_layout.addWidget(btn_choose_map)
        self.lbl_map_path = QLabel("Chưa có bản đồ."); self.lbl_map_path.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 11px;"); self.lbl_map_path.setWordWrap(True)
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

        page_tools = QWidget()
        page_tools_layout = QVBoxLayout(page_tools)
        page_tools_layout.setContentsMargins(10, 15, 10, 15)
        page_tools_layout.setSpacing(8)
        self.tool_category_group = QButtonGroup(self)
        self.tool_category_group.idClicked.connect(self.on_tool_category_changed)
        tools_list = [(0, "🖱️  Con trỏ"), (1, "🖌️  Vẽ tự do"), (2, "⬛  Hình học"), (3, "➖  Đường kẻ"), (4, "🇹  Văn bản")]
        tool_btn_css = "QPushButton { background-color: transparent; color: #f5f6fa; font-weight: bold; font-size: 13px; text-align: left; padding: 10px 5px; border-radius: 6px; border: 1px solid transparent; } QPushButton:hover { background-color: #34495e; } QPushButton:checked { background-color: #e67e22; color: #111111; }"
        for t_id, t_label in tools_list:
            btn = QPushButton(t_label)
            btn.setCheckable(True)
            btn.setStyleSheet(tool_btn_css)
            self.tool_category_group.addButton(btn, t_id)
            page_tools_layout.addWidget(btn)
            if t_id == 0: 
                btn.setChecked(True)
                btn.clicked.connect(lambda checked, t="cursor": self.change_tool(t))
            elif t_id == 1: btn.clicked.connect(lambda checked, t="draw": self.change_tool(t))
            elif t_id == 3: btn.clicked.connect(lambda checked: self.spawn_shape("line"))
        page_tools_layout.addStretch()
        self.sub_panel.addWidget(page_tools)

        middle_layout.addWidget(self.sub_panel)
        middle_layout.addSpacing(5) 

        # --- LỚP 3: BẢN ĐỒ VÀ BẢNG NỔI ---
        self.center_workspace = QFrame()
        self.center_workspace.setStyleSheet("background-color: #111111; border: none; border-radius: 4px;")
        self.center_layout = QVBoxLayout(self.center_workspace)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = InteractiveMapView(self.scene, main_window=self)
        self.view.hide() 
        self.center_layout.addWidget(self.view)
        
        self.lbl_main_map_placeholder = QLabel("🗺️ KHÔNG GIAN HIỂN THỊ BẢN ĐỒ & SA BÀN CHÍNH\n(Mở ngăn 'Bản đồ' ở cột trái để tải ảnh lên)")
        self.lbl_main_map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main_map_placeholder.setStyleSheet("font-size: 16px; color: #7f8c8d; font-weight: bold;")
        self.center_layout.addWidget(self.lbl_main_map_placeholder)

        self.floating_panel = QFrame(self.center_workspace)
        self.floating_panel.setFixedWidth(60)
        self.floating_panel.setFixedHeight(300)
        self.floating_panel.setStyleSheet("QFrame { background-color: #2c3e50; border-radius: 8px; border: 1px solid #1a2228; }")
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
        shapes = [("□", "rect"), ("○", "ellipse"), ("△", "triangle"), ("◇", "diamond"), ("⬠", "pentagon"), ("⬡", "hexagon"), ("☆", "star")]
        for icon, s_id in shapes:
            btn = QPushButton(icon)
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-size: 22px; border-radius: 4px; } QPushButton:hover { background-color: #34495e; } QPushButton:pressed { background-color: #e67e22; color: #111111; }")
            btn.clicked.connect(lambda checked, s=s_id: self.spawn_shape(s))
            scroll_content_layout.addWidget(btn)
        scroll_content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        float_layout.addWidget(scroll_area)
        self.floating_panel.move(10, 10) 
        self.floating_panel.hide() 
        
        middle_layout.addWidget(self.center_workspace, stretch=1)

        # =========================================================================
        # TÁI CẤU TRÚC GIAO DIỆN CỘT PHẢI - FIX LỖI ĐÈ CHỮ TAG
        # =========================================================================
        modern_spinbox_css = """
            QSpinBox {
                background-color: #1e272e; color: #ffffff; 
                border: 1px solid #485460; border-radius: 3px; 
                padding: 2px 4px; font-size: 11px; font-weight: bold;
                min-height: 18px;
            }
            QSpinBox:focus { border: 1px solid #3498db; }
        """

        modern_checkbox_css = """
            QCheckBox { color: #bdc3c7; font-size: 11px; font-weight: bold; spacing: 5px; }
            QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; border: 1px solid #7f8c8d; background-color: #1e272e; }
            QCheckBox::indicator:hover { border: 1px solid #3498db; }
            QCheckBox::indicator:checked { background-color: #e67e22; border: 1px solid #e67e22; }
        """

        modern_label_css = "color: #bdc3c7; font-size: 11px; font-weight: bold;"
        section_title_css = "color: #f1c40f; font-weight: bold; font-size: 12px; text-transform: uppercase; padding-top: 5px; padding-bottom: 2px;"

        right_panel = QFrame()
        right_panel.setFixedWidth(250) 
        right_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 10, 6, 10) 
        right_layout.setSpacing(2)
        
        lbl_right_title = QLabel("⚙️ THUỘC TÍNH")
        lbl_right_title.setStyleSheet("font-weight: bold; border-bottom: 2px solid #34495e; padding-bottom: 4px; color: #f1c40f; font-size: 13px;")
        right_layout.addWidget(lbl_right_title)

        self.right_prop_stack = QStackedWidget()
        
        page_empty = QWidget()
        page_empty_layout = QVBoxLayout(page_empty)
        lbl_properties_hint = QLabel("\n\n(Click vào hình vẽ để cấu hình)")
        lbl_properties_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_properties_hint.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 11px;")
        page_empty_layout.addWidget(lbl_properties_hint)
        page_empty_layout.addStretch()
        self.right_prop_stack.addWidget(page_empty)

        page_props_container = QWidget()
        page_props_layout_main = QVBoxLayout(page_props_container)
        page_props_layout_main.setContentsMargins(0, 0, 0, 0)

        props_scroll = QScrollArea()
        props_scroll.setWidgetResizable(True)
        props_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        props_scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; } 
            QScrollBar:vertical { width: 5px; background: #1e272e; } 
            QScrollBar::handle:vertical { background: #7f8c8d; border-radius: 2px; }
        """)

        page_props = QWidget()
        page_props_layout = QVBoxLayout(page_props)
        page_props_layout.setContentsMargins(2, 2, 8, 2) 
        page_props_layout.setSpacing(8) 

        # --- 1. NHÓM VỊ TRÍ, LỚP ---
        page_props_layout.addWidget(QLabel("📍 THÔNG SỐ CƠ BẢN", styleSheet=section_title_css))
        grid_pos = QGridLayout()
        grid_pos.setSpacing(4) 
        grid_pos.setContentsMargins(0, 0, 0, 0)
        
        LABEL_W = 35
        SPIN_W = 60

        lbl_x = QLabel("Trục X:"); lbl_x.setFixedWidth(LABEL_W); lbl_x.setStyleSheet(modern_label_css)
        self.spin_x = QSpinBox(); self.spin_x.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_x.setFixedWidth(SPIN_W); self.spin_x.setRange(-10000, 10000)
        self.spin_x.setStyleSheet(modern_spinbox_css)
        self.spin_x.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_x, 0, 0)
        grid_pos.addWidget(self.spin_x, 0, 1)

        lbl_y = QLabel("Trục Y:"); lbl_y.setFixedWidth(LABEL_W); lbl_y.setStyleSheet(modern_label_css)
        self.spin_y = QSpinBox(); self.spin_y.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_y.setFixedWidth(SPIN_W); self.spin_y.setRange(-10000, 10000)
        self.spin_y.setStyleSheet(modern_spinbox_css)
        self.spin_y.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_y, 0, 2)
        grid_pos.addWidget(self.spin_y, 0, 3)

        lbl_z = QLabel("Lớp Z:"); lbl_z.setFixedWidth(LABEL_W); lbl_z.setStyleSheet(modern_label_css)
        self.spin_zindex = QSpinBox(); self.spin_zindex.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_zindex.setFixedWidth(SPIN_W); self.spin_zindex.setRange(-1000, 1000)
        self.spin_zindex.setStyleSheet(modern_spinbox_css)
        self.spin_zindex.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_z, 1, 0)
        grid_pos.addWidget(self.spin_zindex, 1, 1)

        lbl_op = QLabel("Mờ(%):"); lbl_op.setFixedWidth(LABEL_W); lbl_op.setStyleSheet(modern_label_css)
        self.spin_opacity = QSpinBox(); self.spin_opacity.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_opacity.setFixedWidth(SPIN_W); self.spin_opacity.setRange(10, 100)
        self.spin_opacity.setStyleSheet(modern_spinbox_css)
        self.spin_opacity.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_op, 1, 2)
        grid_pos.addWidget(self.spin_opacity, 1, 3)

        lbl_w = QLabel("Rộng:"); lbl_w.setFixedWidth(LABEL_W); lbl_w.setStyleSheet(modern_label_css)
        self.spin_width = QSpinBox(); self.spin_width.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_width.setFixedWidth(SPIN_W); self.spin_width.setRange(0, 10000)
        self.spin_width.setStyleSheet(modern_spinbox_css)
        self.spin_width.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_w, 2, 0)
        grid_pos.addWidget(self.spin_width, 2, 1)

        lbl_h = QLabel("Cao:"); lbl_h.setFixedWidth(LABEL_W); lbl_h.setStyleSheet(modern_label_css)
        self.spin_height = QSpinBox(); self.spin_height.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_height.setFixedWidth(SPIN_W); self.spin_height.setRange(0, 10000)
        self.spin_height.setStyleSheet(modern_spinbox_css)
        self.spin_height.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_h, 2, 2)
        grid_pos.addWidget(self.spin_height, 2, 3)

        lbl_rot = QLabel("Góc(°):"); lbl_rot.setFixedWidth(LABEL_W); lbl_rot.setStyleSheet(modern_label_css)
        self.spin_rotation = QSpinBox(); self.spin_rotation.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_rotation.setFixedWidth(SPIN_W); self.spin_rotation.setRange(0, 360)
        self.spin_rotation.setStyleSheet(modern_spinbox_css.replace("color: #ffffff;", "color: #e67e22;"))
        self.spin_rotation.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_rot, 3, 0)
        grid_pos.addWidget(self.spin_rotation, 3, 1)

        grid_pos.setColumnStretch(0, 0); grid_pos.setColumnStretch(1, 1)
        grid_pos.setColumnStretch(2, 0); grid_pos.setColumnStretch(3, 1)
        page_props_layout.addLayout(grid_pos)

        # --- 2. ĐƯỜNG NÉT & MÀU SẮC ---
        page_props_layout.addWidget(QLabel("🎨 GIAO DIỆN", styleSheet=section_title_css))
        grid_style = QGridLayout()
        grid_style.setSpacing(4)
        grid_style.setContentsMargins(0, 0, 0, 0)

        lbl_thick = QLabel("Cỡ nét:"); lbl_thick.setFixedWidth(LABEL_W); lbl_thick.setStyleSheet(modern_label_css)
        self.spin_thickness = QSpinBox(); self.spin_thickness.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_thickness.setFixedWidth(SPIN_W); self.spin_thickness.setRange(1, 30)
        self.spin_thickness.setStyleSheet(modern_spinbox_css)
        self.spin_thickness.valueChanged.connect(self.apply_shape_properties)
        grid_style.addWidget(lbl_thick, 0, 0)
        grid_style.addWidget(self.spin_thickness, 0, 1)

        self.chk_dashed = QCheckBox("Nét đứt")
        self.chk_dashed.setStyleSheet(modern_checkbox_css)
        self.chk_dashed.stateChanged.connect(self.apply_shape_properties)
        grid_style.addWidget(self.chk_dashed, 0, 2, 1, 2)
        
        grid_style.setColumnStretch(0, 0); grid_style.setColumnStretch(1, 1)
        grid_style.setColumnStretch(2, 0); grid_style.setColumnStretch(3, 1)
        page_props_layout.addLayout(grid_style)

        # Bảng màu Viền
        page_props_layout.addWidget(QLabel("Màu viền (Stroke):", styleSheet=modern_label_css))
        color_grid = QGridLayout()
        color_grid.setSpacing(4)
        color_grid.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        colors = ["#ffffff", "#bdc3c7", "#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6", "#000000"]
        c_row, c_col = 0, 0
        for color_hex in colors:
            c_btn = QPushButton()
            c_btn.setFixedSize(20, 20)
            c_btn.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #7f8c8d; border-radius: 3px; }} QPushButton:hover {{ border: 1.5px solid white; }}")
            c_btn.clicked.connect(lambda checked, c=color_hex: self.apply_stroke_color(c))
            color_grid.addWidget(c_btn, c_row, c_col)
            c_col += 1
            if c_col > 5: c_col = 0; c_row += 1
        page_props_layout.addLayout(color_grid)

        # Tô màu nền
        self.chk_fill = QCheckBox("Tô màu nền (Fill)")
        self.chk_fill.setStyleSheet(modern_checkbox_css + "margin-top: 5px;")
        self.chk_fill.stateChanged.connect(self.on_fill_toggled)
        page_props_layout.addWidget(self.chk_fill)

        self.fill_color_container = QWidget()
        fill_color_layout = QVBoxLayout(self.fill_color_container)
        fill_color_layout.setContentsMargins(0, 0, 0, 0)
        
        fill_grid = QGridLayout()
        fill_grid.setSpacing(4)
        fill_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fc_row, fc_col = 0, 0
        for color_hex in colors: 
            fc_btn = QPushButton()
            fc_btn.setFixedSize(20, 20) 
            fc_btn.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #7f8c8d; border-radius: 3px; }} QPushButton:hover {{ border: 1.5px solid white; }}")
            fc_btn.clicked.connect(lambda checked, c=color_hex: self.apply_fill_color(c))
            fill_grid.addWidget(fc_btn, fc_row, fc_col)
            fc_col += 1
            if fc_col > 5: fc_col = 0; fc_row += 1
        
        fill_color_layout.addLayout(fill_grid)
        page_props_layout.addWidget(self.fill_color_container)
        self.fill_color_container.hide() 
        self.current_fill_color = "#3498db" 
        
        # ==========================================
        # 4. KHỐI THÔNG SỐ NHÃN (TAG)
        # ==========================================
        self.tag_container = QFrame()
        self.tag_container.setStyleSheet("background-color: #1a2228; border-radius: 4px; margin-top: 5px; border: 1px solid #34495e;")
        tag_layout = QVBoxLayout(self.tag_container)
        tag_layout.setContentsMargins(6, 6, 6, 6)
        tag_layout.setSpacing(6)
        
        tag_layout.addWidget(QLabel("🏷️ THÔNG SỐ NHÃN", styleSheet=section_title_css.replace("padding-top: 5px;", "border:none;")))
        
        # Tiêu đề ghi chú nội dung
        lbl_tag_content = QLabel("📝 Nội dung:")
        lbl_tag_content.setStyleSheet(modern_label_css)
        tag_layout.addWidget(lbl_tag_content)

        self.txt_tag_text = QLineEdit()
        self.txt_tag_text.setPlaceholderText("Nhập nội dung...")
        self.txt_tag_text.setStyleSheet("background-color: #2c3e50; color: white; padding: 4px; border: 1px solid #485460; border-radius: 3px; font-size: 11px; font-weight: bold;")
        self.txt_tag_text.textChanged.connect(self.apply_tag_properties)
        tag_layout.addWidget(self.txt_tag_text)
        
        # Loại bỏ các giới hạn FixedWidth cho Nhãn để không bị che khuất
        tag_grid = QGridLayout()
        tag_grid.setSpacing(4)
        tag_grid.setContentsMargins(0,0,0,0)
        
        lbl_tag_size = QLabel("Cỡ chữ:"); lbl_tag_size.setStyleSheet(modern_label_css)
        self.spin_tag_size = QSpinBox(); self.spin_tag_size.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_tag_size.setFixedWidth(50); self.spin_tag_size.setRange(8, 48)
        self.spin_tag_size.setStyleSheet(modern_spinbox_css)
        self.spin_tag_size.valueChanged.connect(self.apply_tag_properties)
        tag_grid.addWidget(lbl_tag_size, 0, 0)
        tag_grid.addWidget(self.spin_tag_size, 0, 1)

        lbl_tag_offset = QLabel("Cách lề:"); lbl_tag_offset.setStyleSheet(modern_label_css)
        self.spin_tag_offset = QSpinBox(); self.spin_tag_offset.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_tag_offset.setFixedWidth(50); self.spin_tag_offset.setRange(-100, 500)
        self.spin_tag_offset.setStyleSheet(modern_spinbox_css)
        self.spin_tag_offset.valueChanged.connect(self.apply_tag_properties)
        tag_grid.addWidget(lbl_tag_offset, 0, 2)
        tag_grid.addWidget(self.spin_tag_offset, 0, 3)

        tag_layout.addLayout(tag_grid)

        # Màu NỀN Nhãn
        tag_layout.addWidget(QLabel("Màu nền Nhãn (Background):", styleSheet=modern_label_css))
        tag_bg_grid = QGridLayout()
        tag_bg_grid.setSpacing(4)
        tag_bg_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, color_hex in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(20, 20) 
            btn.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #7f8c8d; border-radius: 3px; }} QPushButton:hover {{ border: 2px solid white; }}")
            btn.clicked.connect(lambda checked, c=color_hex: self.apply_tag_color(c, is_bg=True))
            tag_bg_grid.addWidget(btn, i//6, i%6)
        tag_layout.addLayout(tag_bg_grid)

        # Tính năng mới: Màu CHỮ Nhãn
        tag_layout.addWidget(QLabel("Màu chữ Nhãn (Text):", styleSheet=modern_label_css))
        tag_fg_grid = QGridLayout()
        tag_fg_grid.setSpacing(4)
        tag_fg_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, color_hex in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(20, 20) 
            btn.setStyleSheet(f"QPushButton {{ background-color: {color_hex}; border: 1px solid #7f8c8d; border-radius: 3px; }} QPushButton:hover {{ border: 2px solid white; }}")
            btn.clicked.connect(lambda checked, c=color_hex: self.apply_tag_color(c, is_bg=False))
            tag_fg_grid.addWidget(btn, i//6, i%6)
        tag_layout.addLayout(tag_fg_grid)

        self.btn_del_tag = QPushButton("🗑 Xóa Nhãn")
        self.btn_del_tag.setStyleSheet("QPushButton { background-color: #c0392b; color: white; font-weight: bold; font-size: 11px; padding: 4px; border-radius: 3px; border: none; } QPushButton:hover { background-color: #e74c3c; }")
        self.btn_del_tag.clicked.connect(self.action_remove_tag)
        tag_layout.addWidget(self.btn_del_tag)
        
        page_props_layout.addWidget(self.tag_container)
        self.tag_container.hide() 

        page_props_layout.addStretch()
        props_scroll.setWidget(page_props)
        page_props_layout_main.addWidget(props_scroll)
        self.right_prop_stack.addWidget(page_props_container)

        right_layout.addWidget(self.right_prop_stack)
        middle_layout.addWidget(right_panel)
        main_layout.addWidget(middle_widget, stretch=1)

        # === THANH TIẾN TRÌNH ===
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

    # =========================================================================
    # THANH TÁC VỤ NHANH NỔI (QUICK ACTION BAR) 
    # =========================================================================
    def setup_quick_action_bar(self):
        self.quick_action_bar = QFrame(self.view)
        self.quick_action_bar.setStyleSheet("""
            QFrame { background-color: #1e272e; border-radius: 6px; border: 1px solid #485460; }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8); shadow.setColor(QColor(0, 0, 0, 150)); shadow.setOffset(0, 3)
        self.quick_action_bar.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self.quick_action_bar)
        layout.setContentsMargins(4, 2, 4, 2) 
        layout.setSpacing(2)

        btn_css = """
            QPushButton { 
                background: transparent; color: white; border: none; 
                font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; 
                padding: 4px 8px; border-radius: 4px; font-weight: normal;
            } 
            QPushButton:hover { background-color: #34495e; }
        """

        self.btn_tag = QPushButton("T")
        self.btn_tag.setToolTip("Thêm Nhãn")
        self.btn_tag.setStyleSheet(btn_css)
        self.btn_tag.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        self.btn_tag.clicked.connect(self.action_add_tag)

        self.btn_dup = QPushButton("⧉")
        self.btn_dup.setToolTip("Nhân bản")
        self.btn_dup.setStyleSheet(btn_css)
        self.btn_dup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_dup.clicked.connect(self.action_duplicate)

        self.btn_del = QPushButton("🗑")
        self.btn_del.setToolTip("Xóa")
        self.btn_del.setStyleSheet(btn_css)
        self.btn_del.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_del.clicked.connect(self.action_delete)

        self.btn_more = QPushButton("⋮")
        self.btn_more.setToolTip("Tùy chọn khác")
        self.btn_more.setStyleSheet(btn_css)
        self.btn_more.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.btn_tag)
        layout.addWidget(self.btn_dup)
        layout.addWidget(self.btn_del)
        layout.addWidget(self.btn_more)

        self.quick_action_bar.hide()

    def update_quick_action_bar_pos(self, item):
        """Tính khoảng cách bám sát sạt chuẩn xác"""
        if not item or not item.isSelected():
            self.quick_action_bar.hide()
            return
            
        if self.quick_action_bar.isHidden():
            self.quick_action_bar.show()
            self.quick_action_bar.raise_()

        visual_rect = QRectF(-item.w/2, -item.h/2, item.w, item.h)
        if item.shape_type == 'draw':
            visual_rect = item.path().boundingRect()
            
        scene_polygon = item.mapToScene(visual_rect)
        view_rect = self.view.mapFromScene(scene_polygon).boundingRect()

        bar_w = self.quick_action_bar.sizeHint().width()
        bar_h = self.quick_action_bar.sizeHint().height()

        bar_x = view_rect.center().x() - bar_w / 2
        bar_y = view_rect.top() - bar_h - 2 # Ép sát xuống cách đỉnh vật thể đúng 2px

        bar_x = max(10, min(bar_x, self.view.viewport().width() - bar_w - 10))
        bar_y = max(10, bar_y)
        self.quick_action_bar.move(bar_x, bar_y)

    # --- CHỨC NĂNG CÁC NÚT TÁC VỤ ---
    def action_delete(self):
        items = self.scene.selectedItems()
        if items:
            for item in items:
                self.scene.removeItem(item)
            self.scene.clearSelection()
            self.quick_action_bar.hide()
            self.right_prop_stack.setCurrentIndex(0)

    def action_duplicate(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        
        pen = QPen(item.pen())
        brush = QBrush(item.brush())
        
        # Sao chép chính xác kích thước thật sau khi đã co giãn
        new_item = DraggableShape(item.shape_type, item.w, item.h, pen, brush, initial_path=getattr(item, 'orig_drawn_path', None), main_window=self)
        new_item.setPos(item.x() + 30, item.y() + 30) 
        new_item.setRotation(item.rotation())
        new_item.setZValue(item.zValue())
        new_item.setOpacity(item.opacity())
        
        new_item.has_tag = item.has_tag
        new_item.tag_text = item.tag_text
        new_item.tag_pos = item.tag_pos
        new_item.tag_bg = item.tag_bg
        new_item.tag_fg = item.tag_fg
        new_item.tag_size = item.tag_size
        new_item.tag_offset = item.tag_offset

        self.scene.addItem(new_item)
        self.scene.clearSelection()
        new_item.setSelected(True)

    def action_add_tag(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        item.has_tag = True
        item.prepareGeometryChange() 
        item.update()
        self.update_right_panel_from_item(item)
        self.update_quick_action_bar_pos(item)

    def action_remove_tag(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        item.has_tag = False
        item.prepareGeometryChange() 
        item.update()
        self.update_right_panel_from_item(item)
        self.update_quick_action_bar_pos(item)

    # --- CÁC HÀM SPAWN & THUỘC TÍNH ---
    def spawn_shape(self, shape_id):
        if not self.current_pixmap:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tải bản đồ lên trước khi tạo hình!")
            return

        size = 100 
        center = self.view.mapToScene(self.view.viewport().rect().center())
        pen = QPen(QColor("#bdc3c7"))
        pen.setWidth(3); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        shape_item = DraggableShape(shape_id, size, size if shape_id != "line" else 0, pen, brush=QBrush(Qt.BrushStyle.NoBrush), main_window=self)
        shape_item.setPos(center) 
        
        shape_item.setZValue(0)
        shape_item.setOpacity(1.0)

        self.scene.addItem(shape_item)
        self.scene.clearSelection()
        shape_item.setSelected(True)
        
        self.floating_panel.hide()
        self.tool_category_group.button(0).setChecked(True) 
        self.change_tool("cursor")

    def on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], DraggableShape):
            self.right_prop_stack.setCurrentIndex(1) 
            self.view.active_item = selected[0]
            self.update_right_panel_from_item(selected[0])
            self.update_quick_action_bar_pos(selected[0])
        else:
            self.right_prop_stack.setCurrentIndex(0) 
            self.quick_action_bar.hide()
            self.view.active_item = None

    def update_right_panel_from_item(self, item):
        if not item or not item.isSelected(): return
        
        self.spin_x.blockSignals(True); self.spin_y.blockSignals(True)
        self.spin_zindex.blockSignals(True); self.spin_opacity.blockSignals(True)
        self.spin_width.blockSignals(True); self.spin_height.blockSignals(True)
        self.spin_rotation.blockSignals(True); self.spin_thickness.blockSignals(True)
        self.chk_dashed.blockSignals(True) 
        self.chk_fill.blockSignals(True); self.txt_tag_text.blockSignals(True)
        self.spin_tag_size.blockSignals(True); self.spin_tag_offset.blockSignals(True)
        
        pos = item.scenePos()
        self.spin_x.setValue(int(pos.x())); self.spin_y.setValue(int(pos.y()))
        
        self.spin_zindex.setValue(int(item.zValue()))
        self.spin_opacity.setValue(int(item.opacity() * 100))

        self.spin_rotation.setValue(int(item.rotation() % 360))
        self.spin_thickness.setValue(item.pen().width())
        self.spin_width.setValue(int(item.w))
        self.spin_height.setValue(int(item.h))
        
        self.chk_dashed.setChecked(item.pen().style() == Qt.PenStyle.DashLine)
            
        if item.shape_type in ["line", "draw"]:
            self.chk_fill.hide()
            self.fill_color_container.hide()
            if item.shape_type == "line": self.spin_height.setEnabled(False) 
            else: self.spin_height.setEnabled(True)
        else:
            self.spin_height.setEnabled(True)
            self.chk_fill.show()
            if item.brush().style() != Qt.BrushStyle.NoBrush:
                self.chk_fill.setChecked(True)
                self.fill_color_container.show()
                self.current_fill_color = item.brush().color().name()
            else:
                self.chk_fill.setChecked(False)
                self.fill_color_container.hide()
        
        if item.has_tag:
            self.tag_container.show()
            self.txt_tag_text.setText(item.tag_text)
            self.spin_tag_size.setValue(item.tag_size)
            self.spin_tag_offset.setValue(item.tag_offset)
        else:
            self.tag_container.hide()
            
        self.spin_x.blockSignals(False); self.spin_y.blockSignals(False)
        self.spin_zindex.blockSignals(False); self.spin_opacity.blockSignals(False)
        self.spin_width.blockSignals(False); self.spin_height.blockSignals(False)
        self.spin_rotation.blockSignals(False); self.spin_thickness.blockSignals(False)
        self.chk_dashed.blockSignals(False)
        self.chk_fill.blockSignals(False); self.txt_tag_text.blockSignals(False)
        self.spin_tag_size.blockSignals(False); self.spin_tag_offset.blockSignals(False)

    def apply_shape_properties(self):
        selected = self.scene.selectedItems()
        if not selected or not hasattr(selected[0], 'shape_type'): return
        item = selected[0]
        
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        item.setPos(self.spin_x.value(), self.spin_y.value())
        item.setRotation(self.spin_rotation.value())
        
        item.setZValue(self.spin_zindex.value())
        item.setOpacity(self.spin_opacity.value() / 100.0)

        pen = item.pen()
        pen.setWidth(self.spin_thickness.value())
        if self.chk_dashed.isChecked():
            pen.setStyle(Qt.PenStyle.DashLine)
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)
        item.setPen(pen)

        item.w = self.spin_width.value()
        item.h = self.spin_height.value()
        item.update_path()
            
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.update_quick_action_bar_pos(item)

    def apply_stroke_color(self, hex_color):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        pen = item.pen(); pen.setColor(QColor(hex_color)); item.setPen(pen)

    def on_fill_toggled(self, state):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        if state == Qt.CheckState.Checked.value:
            self.fill_color_container.show()
            item.setBrush(QBrush(QColor(self.current_fill_color)))
        else:
            self.fill_color_container.hide()
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def apply_fill_color(self, hex_color):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        self.current_fill_color = hex_color
        if self.chk_fill.isChecked():
            item.setBrush(QBrush(QColor(hex_color)))

    def apply_tag_properties(self):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        if item.has_tag:
            item.prepareGeometryChange() 
            item.tag_text = self.txt_tag_text.text()
            item.tag_size = self.spin_tag_size.value()
            item.tag_offset = self.spin_tag_offset.value()
            item.update()
            self.update_quick_action_bar_pos(item)
            
    def apply_tag_color(self, hex_color, is_bg=True):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        if item.has_tag:
            if is_bg: item.tag_bg = hex_color
            else: item.tag_fg = hex_color 
            item.update()

    def on_tool_category_changed(self, tool_id):
        if tool_id == 2: self.floating_panel.show(); self.floating_panel.raise_() 
        else: self.floating_panel.hide()

    def change_tool(self, tool_name):
        self.view.current_tool = tool_name
        if tool_name == "cursor": self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else: self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def toggle_grid(self, checked):
        self.view.show_grid = checked; self.display_win.view.show_grid = checked
        self.btn_grid.setText("🌐 Tắt Lưới Tọa Độ" if checked else "🌐 Bật Lưới Tọa Độ"); self.scene.update() 

    def toggle_region_select(self, checked):
        self.view.select_region_mode = checked
        if checked:
            self.btn_region.setText("🎯 Hủy Chọn"); self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.btn_region.setText("🎯 Chọn Vùng Trình Chiếu"); self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def set_projection_region(self, rect):
        if not self.current_pixmap: return
        reply = QMessageBox.question(self, 'Xác nhận Vùng Trình Chiếu', 'Thiết lập đây là khu vực duy nhất sẽ hiển thị trên máy chiếu?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.projection_rect = rect.toRect().intersected(self.current_pixmap.rect())
            if self.projection_frame_item in self.scene.items(): self.scene.removeItem(self.projection_frame_item)
            from PySide6.QtWidgets import QGraphicsRectItem
            self.projection_frame_item = QGraphicsRectItem(self.projection_rect)
            pen = QPen(QColor(230, 126, 34)); pen.setWidth(4); pen.setStyle(Qt.PenStyle.SolidLine) 
            self.projection_frame_item.setPen(pen); self.projection_frame_item.setZValue(9999) 
            self.scene.addItem(self.projection_frame_item)
            self.display_win.view.fitInView(self.projection_rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.btn_region.setChecked(False); self.toggle_region_select(False)

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
            self.current_pixmap = QPixmap(file_path); self.scene.clear() 
            self.scene.addPixmap(self.current_pixmap); self.scene.setSceneRect(self.current_pixmap.rect())
            self.projection_rect = None; self.projection_frame_item = None
            self.lbl_main_map_placeholder.hide(); self.view.show()
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def close_all(self):
        self.display_win.close(); self.close()

    def create_small_btn(self, text, bg_color):
        btn = QPushButton(text)
        btn.setStyleSheet(f"QPushButton {{ background-color: {bg_color}; color: white; font-size: 13px; font-weight: bold; border-radius: 4px; border: none; }} QPushButton:hover {{ background-color: #34495e; border: 1px solid #7f8c8d; }}")
        return btn