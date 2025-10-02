# image_window.py
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt
import os

class ImageWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image")
        self.setFixedSize(551, 248)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.0)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 551, 248)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: transparent;")
        self.show()

    def set_image(self, path: str):
        if not os.path.exists(path):
            self.label.clear()
            return

        img = QImage(path)
        w, h = img.width(), img.height()

        if w <= 551 and h <= 248:
            # 圖片太小就縮放顯示
            pixmap = QPixmap.fromImage(img).scaled(551, 248, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            # 中央裁切
            x = max((w - 551) // 2, 0)
            y = max((h - 248) // 2, 0)
            cropped = img.copy(x, y, min(551, w), min(248, h))
            #pixmap = QPixmap.fromImage(cropped)

        # ⬇️ 將圖片畫進一個新的 QPixmap，並調整透明度
        result = QPixmap(img.size())
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setOpacity(0.9)  # 設定透明度為 60%
        painter.drawImage(0, 0, img)
        painter.end()

        self.label.setPixmap(result)
