# File: main.py
import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_menu import MainMenuWindow

def main():
    app = QApplication(sys.argv)
    
    main_menu = MainMenuWindow()
    # Mở cửa sổ phóng to tối đa nhưng vẫn giữ thanh tiêu đề và Taskbar Windows
    main_menu.showMaximized()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()