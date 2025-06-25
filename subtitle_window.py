import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSizePolicy, QHBoxLayout
from PyQt6.QtGui import QGuiApplication, QPalette, QFont
from PyQt6.QtCore    import Qt, QTimer, QPoint

MAX_W = 1000

class SubtitleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlag(
             Qt.WindowType.FramelessWindowHint |
             Qt.WindowType.WindowStaysOnTopHint
             # Qt.WindowType.Tool # 使用 Tool 類型可以避免在任務欄顯示
        )
        # self.setWindowOpacity(0.0)           # 背景全透，文字不透

        #self.setStyleSheet("background-color: white;")

        # ---- 字幕 QLabel ----
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)                  # 若要截斷就關掉
        self.label.setFixedWidth(MAX_W)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font: 32px "LXGW WenKai";
                background: transparent;
                padding: 10px;
            }
        """)

        # ---- Layout：放底部中央 ----
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        lay.addWidget(self.label,
                      alignment=Qt.AlignmentFlag.AlignHCenter |
                                Qt.AlignmentFlag.AlignBottom)
        lay.setContentsMargins(0, 0, 0, 0)

        self.adjustSize()          # 依第一行文字決定視窗大小
        self._reposition()
        self.show()

    def _reposition(self):
        """把整個視窗移到底邊中央（離底 40px）"""
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) - 40
        )

    # ---- 對外 API ----
    def set_text(self, txt: str):
        if not txt:
            self.resize(1, 1)
            self.showMinimized()
            return

        self.label.setText(txt)
        self.label.adjustSize()    # 先讓 QLabel 跟文字同寬高
        self.adjustSize()          # 父視窗同步縮放
        self._reposition()         # 視窗重新置中於螢幕底
        self.showNormal()

class TitleBannerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Title Banner")

        # ==== 背景設定 ====
        # 讓 OBS 可以擷取，但畫面上看不到（整窗透明）
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)
        self.setFixedSize(1200, 200)
        self.setStyleSheet("background-color: #33ccc9;")

        # === 兩個 label 用來跑同一段字 ===
        self.label1 = QLabel(self)
        self.label2 = QLabel(self)

        for label in (self.label1, self.label2):
            label.setText("歡迎來到成大台灣台，我是主播阿芳，大家可以透過聊天室和我即時互動")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setWordWrap(False)
            label.setFixedHeight(180)  # 避免換行
            label.setStyleSheet("""
                QLabel {
                    color: #d1d1d1;
                    font: 80px "jf open 粉圓";
                    background: transparent;
                    padding: 10px 35px;
                }
            """)
            label.adjustSize()

        # 初始位置
        self.label1.move(0, 20)
        self.label2.move(self.label1.width(), 20)

        # === 計時器滾動字幕 ===
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(20)

        # === 置頂畫面中央 ===
        self._reposition_top()
        self.show()

    def scroll_text(self):
        # 移動兩個 label
        for label in (self.label1, self.label2):
            label.move(label.x() - 2, label.y())

        # 如果 label1 完全離開左邊，放到 label2 的右邊
        if self.label1.x() + self.label1.width() < 0:
            self.label1.move(self.label2.x() + self.label2.width(), self.label1.y())

        # 同理，label2 離開就放到 label1 的右邊
        if self.label2.x() + self.label2.width() < 0:
            self.label2.move(self.label1.x() + self.label1.width(), self.label2.y())

    # -------- 置頂中央（若想整窗靠左，把第一個參數改 0） --------
    def _reposition_top(self):
        screen = QGuiApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, 0)

    # -------- 對外 API：動態設定字幕 --------
    def set_text(self, txt: str):
        if not txt:
            for label in (self.label1, self.label2):
                label.clear()
            self.resize(1, 1)
            self.showMinimized()
            return

        for label in (self.label1, self.label2):
            label.setText(txt)
            label.adjustSize()
        self.label1.move(0, self.label1.y())
        self.label2.move(self.label1.width(), self.label2.y())
        self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TitleBannerWidget()
    win.show()
    sys.exit(app.exec())