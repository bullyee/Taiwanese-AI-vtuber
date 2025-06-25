import asyncio
import os
import random
import re
import threading
from typing import List, Tuple

from PyQt6.QtCore import QTimer
from dotenv import load_dotenv
from twitchio.ext import commands
from playsound import playsound

import audio_vac
from audio_vac import play_wav_to_device, stop_playback
from combine_audio import combine_audio_files, process_and_combine_audio
from scheduler import SubtitleScheduler
from voicevox_tts import generate_greeting_audio
from vts_client import VTSClient


class Bot(commands.Bot):
    def __init__(self,vts: VTSClient, sched: SubtitleScheduler,NewsPool: List[Tuple[str, List[Tuple[str, str | None] ],int ]],DEVICE_ID: int):

        load_dotenv()
        twitch_token = os.environ.get('TWITCH_OAUTH_TOKEN')
        twitch_client_id = os.environ.get('TWITCH_CLIENT_ID')
        twitch_bot_name = os.environ.get('TWITCH_BOT_NAME')
        twitch_channel = os.environ.get('TWITCH_CHANNEL')
        print(twitch_token, twitch_client_id, twitch_bot_name, twitch_channel)

        super().__init__(
            token=twitch_token,
            client_id=twitch_client_id,
            nick=twitch_bot_name,
            prefix='!',
            initial_channels=[twitch_channel]
        )
        self.vts = vts
        self.sched = sched
        self.NewsPool = NewsPool
        self.DEVICE_ID = DEVICE_ID

        self.news_timer = None  # 用於儲存 QTimer 實例
        self.is_playing_news = False  # 標誌新聞是否正在播放
        self.HOTKEY_POOL = [f"My Animation {i}" for i in range(1, 4)]

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        print(f"{message.author.name}: {message.content}")

        # 定義你想要偵測的問候語列表，不區分大小寫
        greeting_keywords = [
            "你好", "Hello", "早安", "午安", "晚安",
            "hi", "hey", "哈囉", "安安", "您好"
        ]

        # 唱歌相關關鍵字
        singing_keywords = [
            "歌", "唱","sing a song"
        ]

        # 年齡相關關鍵字
        age_keywords = [
            "歲", "年紀", "多大", "how old are you", "age","齡"
        ]

        # 介紹類關鍵字 (關鍵詞包和「你會做什麼」意思的字或詞句)
        introduce_keywords = [
            "做什麼","做甚麼" ,"介", "功能", "是誰",
            "what can you do", "introduce yourself", "about you"
        ]

        news_keywords = [
            "news","新聞","報導","播報"
        ]

        stop_keywords = [
            "停","stop","止","休","不要再報"
        ]


        # 將訊息內容轉換為小寫，方便不區分大小寫的匹配
        message_content_lower = message.content.lower()

            # 動作
        def trigger_random_animation():
            hk = random.choice(self.HOTKEY_POOL)
            self.vts.trigger_hotkey(hk)

        # 停止
        if re.search('|'.join(re.escape(k.lower()) for k in stop_keywords), message_content_lower):
            if self.is_playing_news and self.news_timer:
                print("偵測到停止指令，正在停止新聞播報。")
                self.news_timer.stop()  # Stop the QTimer
                self.is_playing_news = False  # Update the flag
                self.sched.clear_queue()  # ⛔ 改用 stop() 而不是只 clear_queue()
                print("完成停止動作")
            else:
                await self.handle_commands(message)
            return  # Crucial: return after handling a command

        # 新聞
        if re.search('|'.join(re.escape(k.lower()) for k in news_keywords), message_content_lower):
            self.news_timer = QTimer()
            self.is_playing_news = True  # 設定標誌為 True
            def play_news():
                title, script ,idx= random.choice(self.NewsPool)
                self.sched.enqueue(title, script,idx)
            self.news_timer.timeout.connect(play_news)
            self.news_timer.start(3 * 60 * 1000)  # 180_000 ms
            self.news_timer.timeout.emit()  # 立刻播第一條（可拿掉）
            await self.handle_commands(message)
            return

        # 1. 偵測唱歌
        if re.search('|'.join(re.escape(k.lower()) for k in singing_keywords), message_content_lower):
            print("偵測到唱歌相關訊息。")
            # 確保 'interact' 目錄存在
            stop_playback()
            os.makedirs("interact", exist_ok=True)
            # 假設 interact/song.wav 存在
            play_wav_to_device("interact_audio/song.wav", self.DEVICE_ID, on_done=None)
            await self.handle_commands(message)
            return  # 處理完畢，不繼續檢查其他條件

        # 2. 偵測年齡相關
        if re.search('|'.join(re.escape(k.lower()) for k in age_keywords), message_content_lower):
            print("偵測到年齡相關訊息。")
            stop_playback()
            os.makedirs("interact", exist_ok=True)
            # 假設 interact/age.wav 存在
            play_wav_to_device("interact_audio/age.wav", self.DEVICE_ID, on_done=None)
            await self.handle_commands(message)
            return  # 處理完畢，不繼續檢查其他條件

        # 3. 偵測介紹類
        if re.search('|'.join(re.escape(k.lower()) for k in introduce_keywords), message_content_lower):
            print("偵測到介紹類訊息。")
            stop_playback()
            os.makedirs("interact", exist_ok=True)
            # 假設 interact/introduce.wav 存在
            play_wav_to_device("interact_audio/introduce.wav", self.DEVICE_ID, on_done=None)
            await self.handle_commands(message)
            return  # 處理完畢，不繼續檢查其他條件

        # 打招呼
        if re.search('|'.join(re.escape(k.lower()) for k in greeting_keywords), message_content_lower):
            random_greet_id = random.randint(1, 6)
            random_name_id = random.randint(1, 3)
            stop_playback()
            await process_and_combine_audio(message.author.name,random_greet_id,random_name_id)
            play_wav_to_device(f"combined_audio/combined_audio_{message.author.name}_{random_greet_id}_{random_name_id}.wav",self.DEVICE_ID,on_done=None)
            await self.handle_commands(message)
            return
