import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSizePolicy, QHBoxLayout
from PyQt6.QtGui import QGuiApplication, QPalette
from PyQt6.QtCore    import Qt

MAX_W = 1000

class SubtitleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)           # 背景全透，文字不透

        # ---- 字幕 QLabel ----
        self.label = QLabel("Count 0", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)                  # 若要截斷就關掉
        self.label.setFixedWidth(MAX_W)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font: 28px "Microsoft JhengHei";
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

        # 如果你要看到背景顏色，**不要**開啟整窗透明
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 半透明/透明可以留著，但要確定有 `WA_StyledBackground`
        # self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)
        self.setFixedSize(1370, 150)

        # ---- 文字 QLabel ----
        self.label = QLabel("中職／悍將需大破尋求大立 拚下半季洋投需Fired for all", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setWordWrap(True)
        self.label.setFixedWidth(1400)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Preferred)  # 讓 label 拉滿寬度
        self.label.setStyleSheet("""
            QLabel {
                color: black;
                font: 50px "Microsoft JhengHei";
                background: transparent;
                padding: 10px 40px;
            }
        """)

        # ---- Layout：置頂靠左 ----
        lay = QHBoxLayout(self)
        lay.addWidget(self.label,
                      alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.setContentsMargins(0, 0, 0, 0)

        # 給整個視窗一個底色
        self.setStyleSheet("background-color: #eb3c1e;")

        self.adjustSize()
        self._reposition_top()
        self.show()

    # -------- 置頂中央（若想整窗貼左，把第一個參數改 0 即可） --------
    def _reposition_top(self):
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(  # 視窗本身仍置中；若要連視窗一起靠左，x 改 0
            (screen.width() - self.width()) // 2,
            0
        )

    # -------- 對外 API --------
    def set_text(self, txt: str):
        if not txt:
            self.label.clear()
            self.resize(1, 1)
            self.showMinimized()
            return

        self.label.setText(txt)
        self.label.adjustSize()
        self.adjustSize()
        self._reposition_top()
        self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TitleBannerWidget()
    win.show()
    sys.exit(app.exec())