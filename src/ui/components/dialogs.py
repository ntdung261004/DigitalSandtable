# File: src/ui/dialogs.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
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