# File: src/ui/editor_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFrame, QLabel, QPushButton, QToolButton, QFileDialog, 
                               QMessageBox, QApplication, QStackedWidget, QButtonGroup,
                               QScrollArea, QGridLayout, QSpinBox, QGraphicsScene,
                               QGraphicsView, QGraphicsItem, QCheckBox, QGraphicsDropShadowEffect, QLineEdit, QSizePolicy)
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush, QIcon, QFontMetrics
from PySide6.QtCore import Qt, QRectF, QPointF, QSize

from src.utils import theme
from src.ui.components.dialogs import InfoDialog
from src.ui.components.projector import DisplayWindow
from src.ui.components.canvas import InteractiveMapView, DraggableShape

class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bộ Biên Tập Sa Bàn Tác Chiến")
        self.sandtable_name = "Sa bàn chưa có tên"
        self.sandtable_scale = "Chưa xác định"
        self.current_pixmap = None 
        self.projection_rect = None 
        self.projection_frame_item = None 
        
        self.showFullScreen()
        
        # CSS Mặc định cho Window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme.MAIN_BG_COLOR}; 
                color: {theme.TITLE_COLOR}; 
                font-family: '{theme.FONT_FAMILY}';
            }}
        """)

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
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(5)

        # =========================================================================
        # 1. THANH TRÊN (TOPBAR)
        # =========================================================================
        top_bar = QFrame()
        top_bar.setFixedHeight(75) 
        top_bar.setStyleSheet(f"background-color: {theme.TOPBAR_BG_COLOR}; border-bottom: 1px solid #111111;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(10)

        self.btn_back = self.create_topbar_btn("home.png", "Về trang chủ", text="Trang chủ")
        self.btn_back.clicked.connect(self.close_all)
        self.btn_undo = self.create_topbar_btn("undo.png", "Hoàn tác (Ctrl+Z)")
        self.btn_redo = self.create_topbar_btn("redo.png", "Làm lại (Ctrl+Y)")

        top_layout.addWidget(self.btn_back)
        top_layout.addSpacing(15)
        top_layout.addWidget(self.btn_undo)
        top_layout.addWidget(self.btn_redo)
        top_layout.addStretch() 

        center_layout = QHBoxLayout()
        center_layout.setSpacing(8)
        self.txt_scenario_title = QLineEdit(self.sandtable_name)
        self.txt_scenario_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_scenario_title.setToolTip("Click vào đây để đổi tên sa bàn")
        self.txt_scenario_title.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; color: #ffffff; 
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; font-size: 18px;
                border: 1px solid transparent; border-radius: 6px; padding: 4px 10px;
                min-width: 240px; 
            }}
            QLineEdit:hover {{ border: 1px solid rgba(255, 255, 255, 0.6); }}
            QLineEdit:focus {{ border: 1px solid #ffffff; background-color: transparent; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """)
        self.txt_scenario_title.textChanged.connect(self.on_title_changed)
        self.txt_scenario_title.editingFinished.connect(self.on_title_edited)
        self.adjust_title_width(self.sandtable_name)

        icon_edit = QLabel()
        icon_edit.setToolTip("Click vào tên để sửa")
        icon_path = os.path.join("assets", "icons", "edit.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_edit.setPixmap(pixmap)
        
        center_layout.addWidget(self.txt_scenario_title)
        center_layout.addWidget(icon_edit)
        top_layout.addLayout(center_layout)
        top_layout.addStretch()

        self.btn_present = self.create_topbar_btn("play.png", "Bắt đầu trình chiếu", text="Thuyết trình")
        self.btn_present.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_present.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: #ffffff; 
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; font-size: 15px;
                padding: 8px 18px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.15); border: 1px solid #ffffff; }}
            QPushButton:pressed {{ background-color: #27ae60; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """)
        self.btn_save = self.create_topbar_btn("save.png", "Lưu hệ thống (Ctrl+S)", text="Lưu")
        
        top_layout.addWidget(self.btn_present)
        top_layout.addSpacing(5)
        top_layout.addWidget(self.btn_save)
        main_layout.addWidget(top_bar)

        # =========================================================================
        # 2. KHU VỰC TRUNG TÂM & SIDEBAR TRÁI
        # =========================================================================
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(5, 5, 5, 5)
        middle_layout.setSpacing(5)

        far_left_bar = QFrame()
        far_left_bar.setFixedWidth(75)
        far_left_bar.setStyleSheet("background-color: #1a2228; border-radius: 4px;")
        far_left_layout = QVBoxLayout(far_left_bar)
        far_left_layout.setContentsMargins(5, 15, 5, 15)
        far_left_layout.setSpacing(15)

        self.main_tab_group = QButtonGroup(self)
        
        # ACTIVE MÀU XANH LÁ CÂY (#27ae60)
        tab_btn_css = f"""
            QToolButton {{ 
                background-color: transparent; color: #bdc3c7; border: 1px solid transparent;
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; border-radius: 8px; padding: 8px 0px; font-size: 11px;
            }}
            QToolButton:hover {{ background-color: #34495e; color: #ffffff; }}
            QToolButton:checked {{ background-color: #27ae60; color: #ffffff; border: 1px solid #2ecc71; }}
        """

        self.btn_tab_map = self.create_sidebar_tab_btn("tab_map.png", "Bản đồ", "🗺️", tab_btn_css)
        self.main_tab_group.addButton(self.btn_tab_map, 0)
        far_left_layout.addWidget(self.btn_tab_map)

        self.btn_tab_tools = self.create_sidebar_tab_btn("tab_tools.png", "Công cụ", "🛠️", tab_btn_css)
        self.main_tab_group.addButton(self.btn_tab_tools, 1)
        far_left_layout.addWidget(self.btn_tab_tools)

        far_left_layout.addStretch()
        middle_layout.addWidget(far_left_bar)

        self.sub_panel = QStackedWidget()
        self.sub_panel.setFixedWidth(160)
        self.sub_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        self.main_tab_group.idClicked.connect(self.sub_panel.setCurrentIndex)

        action_btn_css = f"""
            QPushButton {{ 
                background-color: #1e272e; color: #bdc3c7; 
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; font-size: 12px;
                border-radius: 6px; padding: 10px; border: 1px solid transparent; text-align: left;
            }}
            QPushButton:hover {{ background-color: #34495e; color: #ffffff; border: 1px solid #7f8c8d; }}
            QPushButton:checked, QPushButton:pressed {{ background-color: #27ae60; color: #ffffff; border: 1px solid #2ecc71; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """

        # [Bản Đồ]
        page_map = QWidget()
        page_map_layout = QVBoxLayout(page_map)
        page_map_layout.setContentsMargins(10, 15, 10, 15)
        page_map_layout.setSpacing(10)
        
        btn_choose_map = self.create_icon_btn("folder.png", "Tải bản đồ", "📂", action_btn_css)
        btn_choose_map.clicked.connect(self.choose_map_file)
        page_map_layout.addWidget(btn_choose_map)
        
        self.lbl_map_path = QLabel("Chưa có bản đồ.")
        self.lbl_map_path.setStyleSheet("color: #95a5a6; font-style: italic; font-size: 11px; margin-left: 5px;")
        page_map_layout.addWidget(self.lbl_map_path)
        
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setStyleSheet("color: #485460; margin: 5px 0;")
        page_map_layout.addWidget(line1)
        
        self.btn_grid = self.create_icon_btn("grid.png", "Bật Lưới", "🌐", action_btn_css, is_checkable=True)
        self.btn_grid.clicked.connect(self.toggle_grid)
        page_map_layout.addWidget(self.btn_grid)
        
        self.btn_region = self.create_icon_btn("region.png", "Chọn Vùng", "🎯", action_btn_css, is_checkable=True)
        self.btn_region.clicked.connect(self.toggle_region_select)
        page_map_layout.addWidget(self.btn_region)
        page_map_layout.addStretch()
        self.sub_panel.addWidget(page_map)

        # [Công Cụ]
        page_tools = QWidget()
        page_tools_layout = QVBoxLayout(page_tools)
        page_tools_layout.setContentsMargins(10, 15, 10, 15)
        page_tools_layout.setSpacing(8)
        self.tool_category_group = QButtonGroup(self)
        self.tool_category_group.idClicked.connect(self.on_tool_category_changed)
        
        tools_list = [
            (0, "cursor", "cursor.png", "Con trỏ", "🖱️"), 
            (1, "draw", "draw.png", "Vẽ tự do", "🖌️"), 
            (2, "shapes", "shapes.png", "Hình học", "⬛"), 
            (3, "line", "line.png", "Đường thẳng", "➖"), 
            (4, "text", "text.png", "Văn bản", "🇹")
        ]
        
        tool_btn_css = f"""
            QPushButton {{ 
                background-color: transparent; color: #bdc3c7; 
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; font-size: 12px;
                text-align: left; padding: 10px 5px; border-radius: 6px; border: 1px solid transparent; 
            }} 
            QPushButton:hover {{ background-color: #34495e; color: #ffffff; }} 
            QPushButton:checked {{ background-color: #27ae60; color: #ffffff; border: 1px solid #2ecc71; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """

        for t_id, action_name, icon_name, t_label, fallback in tools_list:
            btn = self.create_icon_btn(icon_name, t_label, fallback, tool_btn_css, is_checkable=True)
            self.tool_category_group.addButton(btn, t_id)
            page_tools_layout.addWidget(btn)
            
            if t_id == 0: btn.setChecked(True)
            if action_name in ["cursor", "draw"]: btn.clicked.connect(lambda checked, t=action_name: self.change_tool(t))
            elif action_name == "line": btn.clicked.connect(lambda checked: self.spawn_shape("line"))
            
        page_tools_layout.addStretch()
        self.sub_panel.addWidget(page_tools)
        middle_layout.addWidget(self.sub_panel)

        self.center_workspace = QFrame()
        self.center_workspace.setStyleSheet("background-color: #111111; border: none; border-radius: 4px;")
        self.center_layout = QVBoxLayout(self.center_workspace)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = InteractiveMapView(self.scene, main_window=self)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view.hide() 
        self.center_layout.addWidget(self.view)
        
        placeholder_widget = QWidget()
        ph_layout = QVBoxLayout(placeholder_widget)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ph_icon = QLabel()
        icon_path = os.path.join("assets", "icons", "map_ph.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            ph_icon.setPixmap(pixmap)
        else:
            ph_icon.setText("🗺️")
            ph_icon.setStyleSheet("font-size: 48px; color: #7f8c8d;")
        ph_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ph_text = QLabel("KHÔNG GIAN HIỂN THỊ BẢN ĐỒ & SA BÀN CHÍNH\n(Mở ngăn 'Bản đồ' ở cột trái để tải ảnh lên)")
        ph_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_text.setStyleSheet(f"font-size: 15px; color: #7f8c8d; font-weight: bold; font-family: '{theme.FONT_FAMILY}'; margin-top: 10px;")
        
        ph_layout.addWidget(ph_icon)
        ph_layout.addWidget(ph_text)
        
        self.lbl_main_map_placeholder = placeholder_widget
        self.center_layout.addWidget(self.lbl_main_map_placeholder)

        # Bảng Nổi Hình Học
        self.floating_panel = QFrame(self.center_workspace)
        self.floating_panel.setFixedWidth(64)
        self.floating_panel.setFixedHeight(320)
        self.floating_panel.setStyleSheet("QFrame { background-color: #2c3e50; border-radius: 8px; border: 1px solid #34495e; }")
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
        
        shape_css = f"""
            QPushButton {{ background-color: transparent; color: #bdc3c7; font-size: 22px; border-radius: 4px; border: 1px solid transparent; }}
            QPushButton:hover {{ background-color: #34495e; color: #ffffff; border: 1px solid #7f8c8d; }}
            QPushButton:pressed {{ background-color: #27ae60; color: #ffffff; }}
        """
        shapes = [("rect", "rect.png", "□"), ("ellipse", "ellipse.png", "○"), ("triangle", "triangle.png", "△"), ("diamond", "diamond.png", "◇"), ("pentagon", "pentagon.png", "⬠"), ("hexagon", "hexagon.png", "⬡"), ("star", "star.png", "☆")]
        for s_id, icon_name, fallback in shapes:
            btn = self.create_icon_btn(icon_name, "", fallback, shape_css, is_checkable=False, icon_size=26)
            btn.setFixedSize(42, 42)
            btn.clicked.connect(lambda checked, s=s_id: self.spawn_shape(s))
            scroll_content_layout.addWidget(btn)
            
        scroll_content_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        float_layout.addWidget(scroll_area)
        self.floating_panel.move(10, 10) 
        self.floating_panel.hide() 
        
        middle_layout.addWidget(self.center_workspace, stretch=1)

        # =========================================================================
        # 3. CỘT PHẢI THUỘC TÍNH
        # =========================================================================
        modern_spinbox_css = f"""
            QSpinBox {{
                background-color: #1e272e; color: #ffffff; font-family: '{theme.FONT_FAMILY}';
                border: 1px solid #485460; border-radius: 3px; padding: 2px 4px; font-size: 10px; font-weight: bold; min-height: 16px;
            }}
            QSpinBox:hover {{ background-color: #34495e; color: #ffffff; border: 1px solid #7f8c8d; }}
            QSpinBox:focus {{ background-color: #27ae60; color: #ffffff; border: 1px solid #2ecc71; }}
        """
        modern_checkbox_css = f"""
            QCheckBox {{ color: #ffffff; font-size: 10px; font-weight: bold; spacing: 5px; font-family: '{theme.FONT_FAMILY}'; }}
            QCheckBox:hover {{ color: #ffffff; }}
            QCheckBox::indicator {{ width: 12px; height: 12px; border-radius: 3px; border: 1px solid #7f8c8d; background-color: #1e272e; }}
            QCheckBox::indicator:hover {{ border: 1px solid #ffffff; background-color: #34495e; }}
            QCheckBox::indicator:checked {{ background-color: #27ae60; border: 1px solid #27ae60; }}
        """
        modern_lineedit_css = f"""
            QLineEdit {{
                background-color: #1e272e; color: #ffffff; font-family: '{theme.FONT_FAMILY}';
                padding: 3px; border: 1px solid #485460; border-radius: 3px; font-size: 10px; font-weight: bold;
            }}
            QLineEdit:hover {{ background-color: #34495e; color: #ffffff; border: 1px solid #7f8c8d; }}
            QLineEdit:focus {{ background-color: #27ae60; color: #ffffff; border: 1px solid #2ecc71; }}
        """
        modern_label_css = f"color: #ffffff; font-size: 10px; font-weight: bold; font-family: '{theme.FONT_FAMILY}';"

        right_panel = QFrame()
        right_panel.setFixedWidth(220) 
        right_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 6, 4, 6) 
        right_layout.setSpacing(2)
        
        lbl_right_title = self.create_section_title("settings.png", "THUỘC TÍNH", "⚙️", 16, is_main=True)
        right_layout.addWidget(lbl_right_title)

        self.right_prop_stack = QStackedWidget()
        page_empty = QWidget()
        page_empty_layout = QVBoxLayout(page_empty)
        lbl_properties_hint = QLabel("\n\n(Click vào hình vẽ để cấu hình)")
        lbl_properties_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_properties_hint.setStyleSheet(f"color: #bdc3c7; font-style: italic; font-size: 10px; font-family: '{theme.FONT_FAMILY}';")
        page_empty_layout.addWidget(lbl_properties_hint)
        page_empty_layout.addStretch()
        self.right_prop_stack.addWidget(page_empty)

        page_props_container = QWidget()
        page_props_layout_main = QVBoxLayout(page_props_container)
        page_props_layout_main.setContentsMargins(0, 0, 0, 0)
        
        props_scroll = QScrollArea()
        props_scroll.setWidgetResizable(True)
        # Ẩn HOÀN TOÀN thanh cuộn dọc và ngang, nhưng vẫn cho phép cuộn chuột
        props_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        props_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        props_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        page_props = QWidget()
        page_props_layout = QVBoxLayout(page_props)
        page_props_layout.setContentsMargins(2, 2, 4, 2) 
        page_props_layout.setSpacing(6) 

        # [CƠ BẢN]
        page_props_layout.addWidget(self.create_section_title("basic.png", "THÔNG SỐ CƠ BẢN", "📍", 14))
        grid_pos = QGridLayout(); grid_pos.setSpacing(4); grid_pos.setContentsMargins(0, 0, 0, 0)
        LABEL_W = 32; SPIN_W = 55 

        lbl_x = QLabel("Trục X:"); lbl_x.setFixedWidth(LABEL_W); lbl_x.setStyleSheet(modern_label_css)
        self.spin_x = QSpinBox(); self.spin_x.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_x.setFixedWidth(SPIN_W); self.spin_x.setRange(-10000, 10000); self.spin_x.setStyleSheet(modern_spinbox_css)
        self.spin_x.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_x, 0, 0); grid_pos.addWidget(self.spin_x, 0, 1)

        lbl_y = QLabel("Trục Y:"); lbl_y.setFixedWidth(LABEL_W); lbl_y.setStyleSheet(modern_label_css)
        self.spin_y = QSpinBox(); self.spin_y.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_y.setFixedWidth(SPIN_W); self.spin_y.setRange(-10000, 10000); self.spin_y.setStyleSheet(modern_spinbox_css)
        self.spin_y.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_y, 0, 2); grid_pos.addWidget(self.spin_y, 0, 3)

        lbl_z = QLabel("Lớp Z:"); lbl_z.setFixedWidth(LABEL_W); lbl_z.setStyleSheet(modern_label_css)
        self.spin_zindex = QSpinBox(); self.spin_zindex.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_zindex.setFixedWidth(SPIN_W); self.spin_zindex.setRange(-1000, 1000); self.spin_zindex.setStyleSheet(modern_spinbox_css)
        self.spin_zindex.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_z, 1, 0); grid_pos.addWidget(self.spin_zindex, 1, 1)

        lbl_op = QLabel("Mờ(%):"); lbl_op.setFixedWidth(LABEL_W); lbl_op.setStyleSheet(modern_label_css)
        self.spin_opacity = QSpinBox(); self.spin_opacity.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_opacity.setFixedWidth(SPIN_W); self.spin_opacity.setRange(10, 100); self.spin_opacity.setStyleSheet(modern_spinbox_css)
        self.spin_opacity.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_op, 1, 2); grid_pos.addWidget(self.spin_opacity, 1, 3)

        lbl_w = QLabel("Rộng:"); lbl_w.setFixedWidth(LABEL_W); lbl_w.setStyleSheet(modern_label_css)
        self.spin_width = QSpinBox(); self.spin_width.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_width.setFixedWidth(SPIN_W); self.spin_width.setRange(0, 10000); self.spin_width.setStyleSheet(modern_spinbox_css)
        self.spin_width.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_w, 2, 0); grid_pos.addWidget(self.spin_width, 2, 1)

        lbl_h = QLabel("Cao:"); lbl_h.setFixedWidth(LABEL_W); lbl_h.setStyleSheet(modern_label_css)
        self.spin_height = QSpinBox(); self.spin_height.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_height.setFixedWidth(SPIN_W); self.spin_height.setRange(0, 10000); self.spin_height.setStyleSheet(modern_spinbox_css)
        self.spin_height.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_h, 2, 2); grid_pos.addWidget(self.spin_height, 2, 3)

        lbl_rot = QLabel("Góc(°):"); lbl_rot.setFixedWidth(LABEL_W); lbl_rot.setStyleSheet(modern_label_css)
        self.spin_rotation = QSpinBox(); self.spin_rotation.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_rotation.setFixedWidth(SPIN_W); self.spin_rotation.setRange(0, 360)
        self.spin_rotation.setStyleSheet(modern_spinbox_css.replace("color: #ffffff;", f"color: {theme.TITLE_COLOR};"))
        self.spin_rotation.valueChanged.connect(self.apply_shape_properties)
        grid_pos.addWidget(lbl_rot, 3, 0); grid_pos.addWidget(self.spin_rotation, 3, 1)

        grid_pos.setColumnStretch(0, 0); grid_pos.setColumnStretch(1, 1); grid_pos.setColumnStretch(2, 0); grid_pos.setColumnStretch(3, 1)
        page_props_layout.addLayout(grid_pos)

        # [GIAO DIỆN]
        page_props_layout.addWidget(self.create_section_title("style.png", "GIAO DIỆN", "🎨", 14))
        grid_style = QGridLayout(); grid_style.setSpacing(4); grid_style.setContentsMargins(0, 0, 0, 0)
        lbl_thick = QLabel("Cỡ nét:"); lbl_thick.setFixedWidth(LABEL_W); lbl_thick.setStyleSheet(modern_label_css)
        self.spin_thickness = QSpinBox(); self.spin_thickness.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_thickness.setFixedWidth(SPIN_W); self.spin_thickness.setRange(1, 30); self.spin_thickness.setStyleSheet(modern_spinbox_css)
        self.spin_thickness.valueChanged.connect(self.apply_shape_properties)
        grid_style.addWidget(lbl_thick, 0, 0); grid_style.addWidget(self.spin_thickness, 0, 1)

        self.chk_dashed = QCheckBox("Nét đứt")
        self.chk_dashed.setStyleSheet(modern_checkbox_css)
        self.chk_dashed.stateChanged.connect(self.apply_shape_properties)
        grid_style.addWidget(self.chk_dashed, 0, 2, 1, 2)
        grid_style.setColumnStretch(0, 0); grid_style.setColumnStretch(1, 1); grid_style.setColumnStretch(2, 0); grid_style.setColumnStretch(3, 1)
        page_props_layout.addLayout(grid_style)

        page_props_layout.addWidget(QLabel("Màu viền (Stroke):", styleSheet=modern_label_css))
        color_grid = QGridLayout(); color_grid.setSpacing(4); color_grid.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        colors = ["#ffffff", "#bdc3c7", "#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6", "#000000"]
        
        btn_color_css = """
            QPushButton {{ background-color: {0}; border: 1px solid #7f8c8d; border-radius: 4px; }} 
            QPushButton:hover {{ border: 2px solid #ffffff; }}
        """
        c_row, c_col = 0, 0
        for color_hex in colors:
            c_btn = QPushButton(); c_btn.setFixedSize(18, 18) 
            c_btn.setStyleSheet(btn_color_css.format(color_hex))
            c_btn.clicked.connect(lambda checked, c=color_hex: self.apply_stroke_color(c))
            color_grid.addWidget(c_btn, c_row, c_col)
            c_col += 1; 
            if c_col > 5: c_col = 0; c_row += 1
        page_props_layout.addLayout(color_grid)

        self.chk_fill = QCheckBox("Tô màu nền (Fill)")
        self.chk_fill.setStyleSheet(modern_checkbox_css + "margin-top: 5px;")
        self.chk_fill.stateChanged.connect(self.on_fill_toggled)
        page_props_layout.addWidget(self.chk_fill)

        self.fill_color_container = QWidget()
        fill_color_layout = QVBoxLayout(self.fill_color_container)
        fill_color_layout.setContentsMargins(0, 0, 0, 0)
        fill_grid = QGridLayout(); fill_grid.setSpacing(4); fill_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fc_row, fc_col = 0, 0
        for color_hex in colors: 
            fc_btn = QPushButton(); fc_btn.setFixedSize(18, 18) 
            fc_btn.setStyleSheet(btn_color_css.format(color_hex))
            fc_btn.clicked.connect(lambda checked, c=color_hex: self.apply_fill_color(c))
            fill_grid.addWidget(fc_btn, fc_row, fc_col)
            fc_col += 1
            if fc_col > 5: fc_col = 0; fc_row += 1
        fill_color_layout.addLayout(fill_grid)
        page_props_layout.addWidget(self.fill_color_container)
        self.fill_color_container.hide(); self.current_fill_color = "#3498db" 
        
        # [THÔNG SỐ NHÃN - TAG]
        self.tag_container = QFrame()
        self.tag_container.setStyleSheet("background-color: #1a2228; border-radius: 4px; margin-top: 5px; border: 1px solid #34495e;")
        tag_layout = QVBoxLayout(self.tag_container)
        tag_layout.setContentsMargins(6, 6, 6, 6); tag_layout.setSpacing(6)
        tag_layout.addWidget(self.create_section_title("tag.png", "THÔNG SỐ NHÃN", "🏷️", 14))
        
        lbl_tag_content = QLabel("Nội dung:")
        lbl_tag_content.setStyleSheet(modern_label_css)
        tag_layout.addWidget(lbl_tag_content)

        self.txt_tag_text = QLineEdit()
        self.txt_tag_text.setPlaceholderText("Nhập nội dung...")
        self.txt_tag_text.setStyleSheet(modern_lineedit_css)
        self.txt_tag_text.textChanged.connect(self.apply_tag_properties)
        tag_layout.addWidget(self.txt_tag_text)
        
        tag_grid = QGridLayout(); tag_grid.setSpacing(4); tag_grid.setContentsMargins(0,0,0,0)
        lbl_tag_size = QLabel("Cỡ chữ:"); lbl_tag_size.setStyleSheet(modern_label_css)
        self.spin_tag_size = QSpinBox(); self.spin_tag_size.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_tag_size.setRange(8, 48); self.spin_tag_size.setStyleSheet(modern_spinbox_css)
        self.spin_tag_size.valueChanged.connect(self.apply_tag_properties)
        tag_grid.addWidget(lbl_tag_size, 0, 0); tag_grid.addWidget(self.spin_tag_size, 0, 1)

        lbl_tag_offset = QLabel("Cách lề:"); lbl_tag_offset.setStyleSheet(modern_label_css)
        self.spin_tag_offset = QSpinBox(); self.spin_tag_offset.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_tag_offset.setRange(-100, 500); self.spin_tag_offset.setStyleSheet(modern_spinbox_css)
        self.spin_tag_offset.valueChanged.connect(self.apply_tag_properties)
        tag_grid.addWidget(lbl_tag_offset, 0, 2); tag_grid.addWidget(self.spin_tag_offset, 0, 3)
        tag_layout.addLayout(tag_grid)

        tag_layout.addWidget(QLabel("Màu nền Nhãn:", styleSheet=modern_label_css))
        tag_bg_grid = QGridLayout(); tag_bg_grid.setSpacing(4); tag_bg_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, color_hex in enumerate(colors):
            btn = QPushButton(); btn.setFixedSize(18, 18) 
            btn.setStyleSheet(btn_color_css.format(color_hex))
            btn.clicked.connect(lambda checked, c=color_hex: self.apply_tag_color(c, is_bg=True))
            tag_bg_grid.addWidget(btn, i//6, i%6)
        tag_layout.addLayout(tag_bg_grid)

        tag_layout.addWidget(QLabel("Màu chữ Nhãn:", styleSheet=modern_label_css))
        tag_fg_grid = QGridLayout(); tag_fg_grid.setSpacing(4); tag_fg_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, color_hex in enumerate(colors):
            btn = QPushButton(); btn.setFixedSize(18, 18) 
            btn.setStyleSheet(btn_color_css.format(color_hex))
            btn.clicked.connect(lambda checked, c=color_hex: self.apply_tag_color(c, is_bg=False))
            tag_fg_grid.addWidget(btn, i//6, i%6)
        tag_layout.addLayout(tag_fg_grid)

        del_tag_css = f"""
            QPushButton {{ 
                background-color: #c0392b; color: white; font-weight: bold; 
                font-size: 10px; font-family: '{theme.FONT_FAMILY}';
                padding: 4px; border-radius: 3px; border: none; 
            }} 
            QPushButton:hover {{ background-color: #e74c3c; }}
            QPushButton:pressed {{ background-color: #27ae60; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """
        self.btn_del_tag = self.create_icon_btn("delete.png", "Xóa Nhãn", "🗑", del_tag_css, icon_size=12)
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
        
        # =========================================================================
        # 4. THANH TIẾN TRÌNH (TIMELINE - KHÔNG ICON)
        # =========================================================================
        bottom_panel = QFrame()
        bottom_panel.setFixedHeight(90) 
        bottom_panel.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(8, 4, 8, 4)
        
        lbl_bottom_title = self.create_section_title("", "TIẾN TRÌNH TÁC CHIẾN", "", is_main=True)
        bottom_layout.addWidget(lbl_bottom_title)
        bottom_layout.addStretch()

        main_layout.addWidget(middle_widget, stretch=1)
        main_layout.addWidget(bottom_panel)
        self.setCentralWidget(main_widget)

    # =========================================================================
    # HÀM TẠO TIÊU ĐỀ SECTION CHỈ DÙNG CHỮ NẾU KHÔNG TRUYỀN ICON
    # =========================================================================
    def create_section_title(self, icon_filename="", text="", fallback_emoji="", icon_size=14, is_main=False):
        container = QFrame()
        layout = QHBoxLayout(container)
        
        if is_main:
            container.setStyleSheet(f"QFrame {{ border-bottom: 2px solid #34495e; padding-bottom: 4px; }} QLabel {{ border: none; }}")
            layout.setContentsMargins(0, 0, 0, 4)
            font_size = "13px"
        else:
            container.setStyleSheet(f"QFrame {{ border: none; padding-top: 2px; padding-bottom: 0px; }} QLabel {{ border: none; }}")
            layout.setContentsMargins(0, 2, 0, 0)
            font_size = "11px"
            
        layout.setSpacing(6)
        
        if icon_filename or fallback_emoji:
            icon_label = QLabel()
            icon_path = os.path.join("assets", "icons", icon_filename)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path).scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(pixmap)
                icon_label.setStyleSheet("border: none; background: transparent;")
            else:
                icon_label.setText(fallback_emoji)
                icon_label.setStyleSheet(f"font-size: {icon_size}px; border: none; background: transparent; color: #ffffff;")
            layout.addWidget(icon_label)
            
        text_label = QLabel(text)
        text_label.setStyleSheet(f"color: {theme.TITLE_COLOR}; font-weight: bold; font-size: {font_size}; text-transform: uppercase; font-family: '{theme.FONT_FAMILY}'; border: none; background: transparent;")
        
        layout.addWidget(text_label)
        layout.addStretch()
        return container

    # =========================================================================
    # CÁC HÀM XỬ LÝ HÌNH ẢNH ICON CHUẨN MỰC
    # =========================================================================
    def create_icon_btn(self, icon_filename, text, fallback_text, css, is_checkable=False, icon_size=16):
        btn = QPushButton()
        btn.setCheckable(is_checkable)
        btn.setStyleSheet(css)
        icon_path = os.path.join("assets", "icons", icon_filename)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(icon_size, icon_size))
            if text: btn.setText(f"  {text}")
        else:
            btn.setText(f"{fallback_text}  {text}" if text else fallback_text)
        return btn

    def create_sidebar_tab_btn(self, icon_filename, text, fallback_text, css):
        btn = QToolButton()
        btn.setCheckable(True)
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn.setStyleSheet(css)
        icon_path = os.path.join("assets", "icons", icon_filename)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(22, 22))
            btn.setText(text)
        else:
            btn.setText(f"{fallback_text}\n{text}")
        return btn

    def create_topbar_btn(self, icon_filename, tooltip, text=""):
        btn = QPushButton(text) if text else QPushButton()
        btn.setToolTip(tooltip)
        icon_path = os.path.join("assets", "icons", icon_filename)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: #ffffff;
                font-family: '{theme.FONT_FAMILY}'; font-weight: bold; font-size: 13px;
                border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.3); padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15); border: 1px solid #ffffff;
            }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """)
        return btn

    # =========================================================================
    # CÁC LOGIC TÊN & THANH QUICK ACTION 
    # =========================================================================
    def adjust_title_width(self, text):
        fm = QFontMetrics(self.txt_scenario_title.font())
        width = fm.horizontalAdvance(text) + 40 
        self.txt_scenario_title.setFixedWidth(max(220, min(width, 600)))

    def on_title_changed(self, text):
        self.adjust_title_width(text)
        new_title = text.strip()
        if new_title: self.sandtable_name = new_title

    def on_title_edited(self):
        new_title = self.txt_scenario_title.text().strip()
        if not new_title: self.txt_scenario_title.setText(self.sandtable_name)
        self.txt_scenario_title.clearFocus()

    def setup_quick_action_bar(self):
        self.quick_action_bar = QFrame(self.view)
        self.quick_action_bar.setStyleSheet("QFrame { background-color: #1e272e; border-radius: 6px; border: 1px solid #485460; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8); shadow.setColor(QColor(0, 0, 0, 150)); shadow.setOffset(0, 3)
        self.quick_action_bar.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self.quick_action_bar)
        layout.setContentsMargins(4, 2, 4, 2); layout.setSpacing(2)

        # Sửa màu nền Tooltip thành Vàng Chữ đen ở Action bar
        btn_css = f"""
            QPushButton {{ background: transparent; color: #ffffff; border: none; font-family: '{theme.FONT_FAMILY}'; font-size: 13px; font-weight: bold; padding: 6px; border-radius: 4px; }} 
            QPushButton:hover {{ background-color: #34495e; color: white; }} 
            QPushButton:pressed {{ background-color: #27ae60; color: white; }}
            QToolTip {{ background-color: #F1C40F; color: #111111; border: 1px solid #d4ac0d; border-radius: 4px; padding: 4px; font-size: 12px; font-weight: bold; }}
        """
        
        self.btn_tag = self.create_icon_btn("tag_add.png", "", "T", btn_css, icon_size=16)
        self.btn_tag.setToolTip("Thêm Nhãn"); self.btn_tag.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.btn_tag.clicked.connect(self.action_add_tag)
        
        self.btn_dup = self.create_icon_btn("duplicate.png", "", "⧉", btn_css, icon_size=16)
        self.btn_dup.setToolTip("Nhân bản"); self.btn_dup.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.btn_dup.clicked.connect(self.action_duplicate)
        
        self.btn_del = self.create_icon_btn("delete.png", "", "🗑", btn_css, icon_size=16)
        self.btn_del.setToolTip("Xóa"); self.btn_del.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.btn_del.clicked.connect(self.action_delete)
        
        self.btn_more = self.create_icon_btn("more.png", "", "⋮", btn_css, icon_size=16)
        self.btn_more.setToolTip("Tùy chọn khác"); self.btn_more.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.btn_tag); layout.addWidget(self.btn_dup); layout.addWidget(self.btn_del); layout.addWidget(self.btn_more)
        self.quick_action_bar.hide()

    def update_quick_action_bar_pos(self, item):
        if not item or not item.isSelected():
            self.quick_action_bar.hide(); return
        if self.quick_action_bar.isHidden():
            self.quick_action_bar.show(); self.quick_action_bar.raise_()

        visual_rect = QRectF(-item.w/2, -item.h/2, item.w, item.h)
        if item.shape_type == 'draw': visual_rect = item.path().boundingRect()
            
        scene_polygon = item.mapToScene(visual_rect)
        view_rect = self.view.mapFromScene(scene_polygon).boundingRect()

        bar_w = self.quick_action_bar.sizeHint().width()
        bar_h = self.quick_action_bar.sizeHint().height()

        bar_x = view_rect.center().x() - bar_w / 2
        bar_y = view_rect.top() - bar_h - 2 

        bar_x = max(10, min(bar_x, self.view.viewport().width() - bar_w - 10))
        bar_y = max(10, bar_y)
        self.quick_action_bar.move(bar_x, bar_y)

    def action_delete(self):
        items = self.scene.selectedItems()
        if items:
            for item in items: self.scene.removeItem(item)
            self.scene.clearSelection()
            self.quick_action_bar.hide()
            self.right_prop_stack.setCurrentIndex(0)

    def action_duplicate(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        pen = QPen(item.pen()); brush = QBrush(item.brush())
        new_item = DraggableShape(item.shape_type, item.w, item.h, pen, brush, initial_path=getattr(item, 'orig_drawn_path', None), main_window=self)
        new_item.setPos(item.x() + 30, item.y() + 30); new_item.setRotation(item.rotation()); new_item.setZValue(item.zValue()); new_item.setOpacity(item.opacity())
        new_item.has_tag = item.has_tag; new_item.tag_text = item.tag_text; new_item.tag_pos = item.tag_pos; new_item.tag_bg = item.tag_bg; new_item.tag_fg = item.tag_fg; new_item.tag_size = item.tag_size; new_item.tag_offset = item.tag_offset
        self.scene.addItem(new_item); self.scene.clearSelection(); new_item.setSelected(True)

    def action_add_tag(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        item.has_tag = True; item.prepareGeometryChange(); item.update()
        self.update_right_panel_from_item(item); self.update_quick_action_bar_pos(item)

    def action_remove_tag(self):
        items = self.scene.selectedItems()
        if not items: return
        item = items[0]
        item.has_tag = False; item.prepareGeometryChange(); item.update()
        self.update_right_panel_from_item(item); self.update_quick_action_bar_pos(item)

    def spawn_shape(self, shape_id):
        if not self.current_pixmap:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tải bản đồ lên trước khi tạo hình!")
            return
        size = 100 
        center = self.view.mapToScene(self.view.viewport().rect().center())
        pen = QPen(QColor("#bdc3c7")); pen.setWidth(3); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        shape_item = DraggableShape(shape_id, size, size if shape_id != "line" else 0, pen, brush=QBrush(Qt.BrushStyle.NoBrush), main_window=self)
        shape_item.setPos(center); shape_item.setZValue(0); shape_item.setOpacity(1.0)
        self.scene.addItem(shape_item); self.scene.clearSelection(); shape_item.setSelected(True)
        self.floating_panel.hide(); self.tool_category_group.button(0).setChecked(True); self.change_tool("cursor")

    def on_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], DraggableShape):
            self.right_prop_stack.setCurrentIndex(1); self.view.active_item = selected[0]
            self.update_right_panel_from_item(selected[0]); self.update_quick_action_bar_pos(selected[0])
        else:
            self.right_prop_stack.setCurrentIndex(0); self.quick_action_bar.hide(); self.view.active_item = None

    def update_right_panel_from_item(self, item):
        if not item or not item.isSelected(): return
        self.spin_x.blockSignals(True); self.spin_y.blockSignals(True); self.spin_zindex.blockSignals(True); self.spin_opacity.blockSignals(True)
        self.spin_width.blockSignals(True); self.spin_height.blockSignals(True); self.spin_rotation.blockSignals(True); self.spin_thickness.blockSignals(True)
        self.chk_dashed.blockSignals(True); self.chk_fill.blockSignals(True); self.txt_tag_text.blockSignals(True); self.spin_tag_size.blockSignals(True); self.spin_tag_offset.blockSignals(True)
        
        pos = item.scenePos()
        self.spin_x.setValue(int(pos.x())); self.spin_y.setValue(int(pos.y())); self.spin_zindex.setValue(int(item.zValue())); self.spin_opacity.setValue(int(item.opacity() * 100))
        self.spin_rotation.setValue(int(item.rotation() % 360)); self.spin_thickness.setValue(item.pen().width())
        self.spin_width.setValue(int(item.w)); self.spin_height.setValue(int(item.h))
        self.chk_dashed.setChecked(item.pen().style() == Qt.PenStyle.DashLine)
            
        if item.shape_type in ["line", "draw"]:
            self.chk_fill.hide(); self.fill_color_container.hide()
            if item.shape_type == "line": self.spin_height.setEnabled(False) 
            else: self.spin_height.setEnabled(True)
        else:
            self.spin_height.setEnabled(True); self.chk_fill.show()
            if item.brush().style() != Qt.BrushStyle.NoBrush:
                self.chk_fill.setChecked(True); self.fill_color_container.show(); self.current_fill_color = item.brush().color().name()
            else:
                self.chk_fill.setChecked(False); self.fill_color_container.hide()
        
        if item.has_tag:
            self.tag_container.show(); self.txt_tag_text.setText(item.tag_text)
            self.spin_tag_size.setValue(item.tag_size); self.spin_tag_offset.setValue(item.tag_offset)
        else:
            self.tag_container.hide()
            
        self.spin_x.blockSignals(False); self.spin_y.blockSignals(False); self.spin_zindex.blockSignals(False); self.spin_opacity.blockSignals(False)
        self.spin_width.blockSignals(False); self.spin_height.blockSignals(False); self.spin_rotation.blockSignals(False); self.spin_thickness.blockSignals(False)
        self.chk_dashed.blockSignals(False); self.chk_fill.blockSignals(False); self.txt_tag_text.blockSignals(False); self.spin_tag_size.blockSignals(False); self.spin_tag_offset.blockSignals(False)

    def apply_shape_properties(self):
        selected = self.scene.selectedItems()
        if not selected or not hasattr(selected[0], 'shape_type'): return
        item = selected[0]
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        item.setPos(self.spin_x.value(), self.spin_y.value()); item.setRotation(self.spin_rotation.value()); item.setZValue(self.spin_zindex.value()); item.setOpacity(self.spin_opacity.value() / 100.0)

        pen = item.pen(); pen.setWidth(self.spin_thickness.value())
        if self.chk_dashed.isChecked(): pen.setStyle(Qt.PenStyle.DashLine)
        else: pen.setStyle(Qt.PenStyle.SolidLine)
        item.setPen(pen); item.w = self.spin_width.value(); item.h = self.spin_height.value(); item.update_path()
            
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.update_quick_action_bar_pos(item)

    def apply_stroke_color(self, hex_color):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]; pen = item.pen(); pen.setColor(QColor(hex_color)); item.setPen(pen)

    def on_fill_toggled(self, state):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        if state == Qt.CheckState.Checked.value:
            self.fill_color_container.show(); item.setBrush(QBrush(QColor(self.current_fill_color)))
        else:
            self.fill_color_container.hide(); item.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def apply_fill_color(self, hex_color):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]; self.current_fill_color = hex_color
        if self.chk_fill.isChecked(): item.setBrush(QBrush(QColor(hex_color)))

    def apply_tag_properties(self):
        selected = self.scene.selectedItems()
        if not selected: return
        item = selected[0]
        if item.has_tag:
            item.prepareGeometryChange(); item.tag_text = self.txt_tag_text.text(); item.tag_size = self.spin_tag_size.value(); item.tag_offset = self.spin_tag_offset.value(); item.update(); self.update_quick_action_bar_pos(item)
            
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
        self.btn_grid.setText("  Tắt Lưới" if checked else "  Bật Lưới"); self.scene.update() 

    def toggle_region_select(self, checked):
        self.view.select_region_mode = checked
        if checked: self.btn_region.setText("  Hủy Chọn"); self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else: self.btn_region.setText("  Chọn Vùng"); self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

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