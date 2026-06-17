# File: src/ui/components/projector.py

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
from src.ui.components.canvas import InteractiveMapView

class DisplayWindow(QMainWindow):
    def __init__(self, scene):
        super().__init__()
        self.setWindowTitle("Sa bàn - Trình chiếu")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #000000;")
        self.view = InteractiveMapView(scene, is_projector=True)
        self.setCentralWidget(self.view)