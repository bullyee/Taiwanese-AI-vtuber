# scheduler.py
from __future__ import annotations
from typing import List, Tuple, Callable
import audio_vac
from audio_vac import stop_playback

Step   = Tuple[str, str | None]      # (字幕, wav 或 None)
Script = List[Step]
Item   = Tuple[str, Script]          # (標題, 整份腳本)

class SubtitleScheduler:
    """
    佇列式播放 (字幕, 音檔)；每份腳本可附一個標題。
    - 不再 import GUI，只透過 callback 與外界互動。
    """

    def __init__(
        self,
        device_id: int,
        set_text : Callable[[str], None],
        set_title: Callable[[str], None],
        set_image: Callable[[str], None]  # ✅ 新增
    ):
        self.device_id  = device_id
        self.set_text   = set_text
        self.set_title  = set_title      # <─ 修正變數名
        self.set_image = set_image      # Mys
        self.queue: List[Item] = []
        self.busy = False
        self.image_index = 0    # Mys
        self.stop_flag = False

    # ────────── Public API ──────────
    def enqueue(self, title: str, script: Script) -> None:
        """把 (標題, 腳本) 丟進佇列；若空檔就立即播放。"""
        print(f"Enqueued new script: {title!r}")
        self.queue.append((title, script))
        if not self.busy:
            self._next_script()

    def clear_queue(self):
        print("⛔ 停止字幕播放")
        stop_playback()
        print("1")
        self.stop_flag = True
        print("2")
        self.queue.clear()
        print("3")
        self.busy = False
        print("4")
        # self.set_text("")
        print("5")
        # self.set_title("")
        print("6")

    # ────────── Internal ──────────
    def _next_script(self) -> None:
        """撥下一份腳本；若佇列空則收尾。"""
        if not self.queue:
            self.busy = False
            self.set_text("")
            self.set_title("")       # 清空標題
            return

        self.busy = True
        title, script = self.queue.pop(0)
        self.image_index += 1       #Mys
        self.set_title(title)        # 更新標題

        image_path = f"images/news{self.image_index}_image.jpg"
        self.set_image(image_path)  # ✅ 根據第幾篇切圖片

        self._play_step(script, 0)   # 從第一句開始

    def _play_step(self, script: Script, idx: int) -> None:
        if self.stop_flag:
            print("⛔ 中斷目前腳本播放")
            self.stop_flag = False  # reset
            self.busy = False
            # self.set_text("")
            # self.set_title("")
            return
        """遞迴播放腳本中的每一段，結束後自動切下份腳本。"""
        if idx >= len(script):       # 本腳本播畢 → 換下一份
            self._next_script()
            return

        text, wav = script[idx]
        self.set_text(text)          # 更新字幕

        def _after() -> None:
            self._play_step(script, idx + 1)

        if wav:
            audio_vac.play_wav_to_device(wav, self.device_id, on_done=_after)
        else:
            _after()
