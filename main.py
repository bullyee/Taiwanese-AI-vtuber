import sys, traceback, threading
def _thread_excepthook(args):
    print("⚠️  Unhandled exception in thread:", args.thread.name)
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
    # optional: sys.exit(1)  ← 讓程式結束 + 有 traceback

threading.excepthook = _thread_excepthook

import json
import sys, random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import QTimer

from subtitle_window import SubtitleWindow, TitleBannerWidget
from scheduler        import SubtitleScheduler
from vts_client       import VTSClient
from typing import List, Tuple, Dict, Any
from pathlib import Path

# ---------- 可自訂池子 ----------
Step   = Tuple[str, str | None]   # (字幕, wav or None)
Script = List[Step]               # 整篇新聞
NewsPool: List[Tuple[str, Script]] = []   # (標題, script)

data: List[Dict[str, Any]] = json.loads(Path("news.json").read_text(encoding="utf-8"))

for art in data:
    title = art["title"]
    idx   = art["news_idx"]                   # 1, 2, 3 …

    # 依段號排序，組成 [(text, wav)]
    script: Script = [
        (text, f"audio/news{idx}_{para}.wav")
        for para, text in sorted(
            art["content"].items(), key=lambda kv: int(kv[0])
        )
    ]

    NewsPool.append((title, script))

print(f"已載入 {len(NewsPool)} 篇新聞")
HOTKEY_POOL = [f"My Animation {i}" for i in range(1, 11)]

VAC_ID   = 13               # list_devices() 查到的 index
DEVICE_ID = VAC_ID

# ---------- 啟動三大物件 ----------
app  = QApplication(sys.argv)
win  = SubtitleWindow()
banner = TitleBannerWidget()
vts  = VTSClient()
sched = SubtitleScheduler(device_id=DEVICE_ID, set_text=win.set_text, set_title = banner.set_text)

# ---------- 3 分鐘新聞 ----------
news_timer = QTimer()
def play_news():
    title, script = random.choice(NewsPool)
    sched.enqueue(title, script)
news_timer.timeout.connect(play_news)
news_timer.start(3 * 60 * 1000)          # 180_000 ms
news_timer.timeout.emit()                # 立刻播第一條（可拿掉）

# ---------- 20 秒 VTS 動畫 ----------
anim_timer = QTimer()
def trigger_random_animation():
    hk = random.choice(HOTKEY_POOL)
    vts.trigger_hotkey(hk)
anim_timer.timeout.connect(trigger_random_animation)
anim_timer.start(45 * 1000)

# ---------- 執行 ----------
sys.exit(app.exec())
