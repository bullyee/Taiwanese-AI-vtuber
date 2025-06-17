# scheduler.py
from __future__ import annotations
from typing import List, Tuple, Callable
import audio_vac

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
        set_title: Callable[[str], None]
    ):
        self.device_id  = device_id
        self.set_text   = set_text
        self.set_title  = set_title      # <─ 修正變數名
        self.queue: List[Item] = []
        self.busy = False

    # ────────── Public API ──────────
    def enqueue(self, title: str, script: Script) -> None:
        """把 (標題, 腳本) 丟進佇列；若空檔就立即播放。"""
        print(f"Enqueued new script: {title!r}")
        self.queue.append((title, script))
        if not self.busy:
            self._next_script()

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
        self.set_title(title)        # 更新標題
        self._play_step(script, 0)   # 從第一句開始

    def _play_step(self, script: Script, idx: int) -> None:
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
