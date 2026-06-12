# File: src/utils/theme.py
import os

# --- 1. CẤU HÌNH ẢNH NỀN ---
# Tạm thời sử dụng bando1 làm nền chìm. Bạn có thể đổi sang ảnh logo đơn vị sau này.
BG_IMAGE_PATH = os.path.join("assets", "background.jpg") 
BG_IMAGE_OPACITY = 0.5  # Độ mờ của ảnh nền (từ 0.0 đến 1.0, số càng nhỏ càng chìm)
MAIN_BG_COLOR = "#1e272e" # Màu nền chính (Dark theme)

# --- 2. CẤU HÌNH FONT CHỮ & TIÊU ĐỀ ---
FONT_FAMILY = "Segoe UI" # Font mặc định hiện đại của Windows
TITLE_FONT_SIZE = "36px"
TITLE_COLOR = "#F1D823"
TITLE_FONT_WEIGHT = "bold"

# --- 3. CẤU HÌNH NÚT BẤM (BUTTONS) ---
BTN_WIDTH = 350
BTN_HEIGHT = 65
BTN_FONT_SIZE = "18px"
BTN_FONT_WEIGHT = "bold"
BTN_BORDER_RADIUS = "8px"

# Màu sắc nút ở trạng thái Bình thường
BTN_BG_COLOR = "#032B11"
BTN_TEXT_COLOR = "#F1D823"
BTN_BORDER_COLOR = "#718093"

# Màu sắc nút khi Di chuột vào (Hover)
BTN_HOVER_BG_COLOR = "#EF1212"
BTN_HOVER_BORDER_COLOR = "#F1D823"

# Màu sắc nút khi Bấm (Pressed)
BTN_PRESSED_BG_COLOR = "#EF1212"