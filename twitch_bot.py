import asyncio
import json
import os
import random
import re
import threading
import openai
from typing import List, Tuple

import requests
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

openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

def classify_message_sync(message: str) -> str:
    prompt = f"""你是一位女性實況主播主要在成大台灣台直播，請根據觀眾說的話，做兩件事：

1️⃣ 判斷一個最適合的「回應類型」標籤（只輸出一個標籤字串）  
2️⃣ 用很生活化口語、像是老朋友打屁一般的口吻給出一句簡短回應（不要太長）

標籤如下：
- greet：打招呼
- song：觀眾要聽你唱歌(注意你會的歌只有阿嘛的話一首)
- age：問你幾歲(你24歲)
- introduce：問你是誰 / 功能是什麼(你是日本來台灣留學的大學生，你叫阿芳)
- stop：要你停止播報新聞
- news：要求你播新聞
- nod：肯定、同意、贊成、點頭
- shake：否定、不同意、搖頭
- happy：開心、讚嘆、喜歡、笑(如過那個人分享自己有趣的經驗和回憶或是他做到一件很棒的事情請開心)
- confuse：好奇、沒聽過的(有人如果講任何學術的東西就請困惑)
- despise：嘲諷、不屑、無語、鄙視、糗事(看到咖哩不拌的人請鄙視、不吃香菜也請鄙視)
- none：當你覺得以上標籤都怎麼對到的時候

觀眾說：「{message}」
小心你的reply不要有特殊字元，不要用表情符號
請用這個 JSON 格式回應（只需要這樣）：
{{
  "label": "<分類標籤>",
  "reply": "<你想說的一句話>"
}}"""

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",  # Optional for ranking
        "X-Title": "VTuberBot",              # Optional for ranking
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            data=json.dumps(payload))
        res.raise_for_status()
        result = res.json()
        # label = result["choices"][0]["message"]["content"].strip().lower()
        # print("🧠 分類結果:", label)
        # return label
        content = result["choices"][0]["message"]["content"]
        print("🧠 原始回應：", content)

        # 解析 AI 回傳的 JSON 字串
        decision = json.loads(content)
        label = decision.get("label", "none").strip().lower()
        reply = decision.get("reply", "").strip()

        return label, reply

    except Exception as e:
        print("❌ 分類失敗:", e)
        return "none"

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

        # # 定義你想要偵測的問候語列表，不區分大小寫
        # greeting_keywords = [
        #     "你好", "Hello", "早安", "午安", "晚安",
        #     "hi", "hey", "哈囉", "安安", "您好"
        # ]
        #
        # # 唱歌相關關鍵字
        # singing_keywords = [
        #     "歌", "唱","sing a song"
        # ]
        #
        # # 年齡相關關鍵字
        # age_keywords = [
        #     "歲", "年紀", "多大", "how old are you", "age","齡"
        # ]
        #
        # # 介紹類關鍵字 (關鍵詞包和「你會做什麼」意思的字或詞句)
        # introduce_keywords = [
        #     "做什麼","做甚麼" ,"介", "功能", "是誰",
        #     "what can you do", "introduce yourself", "about you"
        # ]
        #
        # news_keywords = [
        #     "news","新聞","報導","播報"
        # ]
        #
        # stop_keywords = [
        #     "停","stop","止","休","不要再報"
        # ]
        #
        #
        #
        #
        # # 將訊息內容轉換為小寫，方便不區分大小寫的匹配
        # message_content_lower = message.content.lower()
        #
        # # 動作
        # def trigger_random_animation():
        #     hk = random.choice(self.HOTKEY_POOL)
        #     self.vts.trigger_hotkey(hk)
        #
        # # 🔹 角色動作觸發區
        # if re.search(r"點頭|yes|好|同意|贊成|嗯|點個頭", message_content_lower):
        #     print("✅ 偵測到點頭指令")
        #     self.vts.nod_head()
        #     await self.handle_commands(message)
        #     return
        #
        # if re.search(r"搖頭|no|不要|不同意|否定|不行|不准", message_content_lower):
        #     print("✅ 偵測到搖頭指令")
        #     self.vts.shake_head()
        #     await self.handle_commands(message)
        #     return
        #
        # if re.search(r"鄙視|看不起|切|哼|嘖|什麼鬼|低級|無言", message_content_lower):
        #     print("✅ 偵測到鄙視指令")
        #     self.vts.despise()
        #     await self.handle_commands(message)
        #     return
        #
        # if re.search(r"開心|快樂|爽|笑死|喜歡|好耶|哈|嗨起來", message_content_lower):
        #     print("✅ 偵測到開心指令")
        #     self.vts.happy()
        #     await self.handle_commands(message)
        #     return
        #
        # if re.search(r"困惑|疑惑|不懂|？？|為什麼|問號|不解|confused|what", message_content_lower):
        #     print("✅ 偵測到困惑指令")
        #     self.vts.confuse()
        #     await self.handle_commands(message)
        #     return
        #
        # # 停止
        # if re.search('|'.join(re.escape(k.lower()) for k in stop_keywords), message_content_lower):
        #     if self.is_playing_news and self.news_timer:
        #         print("偵測到停止指令，正在停止新聞播報。")
        #         self.news_timer.stop()  # Stop the QTimer
        #         self.is_playing_news = False  # Update the flag
        #         self.sched.clear_queue()  # ⛔ 改用 stop() 而不是只 clear_queue()
        #         print("完成停止動作")
        #     else:
        #         await self.handle_commands(message)
        #     return  # Crucial: return after handling a command
        #
        # # 新聞
        # if re.search('|'.join(re.escape(k.lower()) for k in news_keywords), message_content_lower):
        #     self.news_timer = QTimer()
        #     self.is_playing_news = True  # 設定標誌為 True
        #     def play_news():
        #         title, script ,idx= random.choice(self.NewsPool)
        #         self.sched.enqueue(title, script,idx)
        #     self.news_timer.timeout.connect(play_news)
        #     self.news_timer.start(3 * 60 * 1000)  # 180_000 ms
        #     self.news_timer.timeout.emit()  # 立刻播第一條（可拿掉）
        #     await self.handle_commands(message)
        #     return
        #
        # # 1. 偵測唱歌
        # if re.search('|'.join(re.escape(k.lower()) for k in singing_keywords), message_content_lower):
        #     print("偵測到唱歌相關訊息。")
        #     # 確保 'interact' 目錄存在
        #     stop_playback()
        #     os.makedirs("interact", exist_ok=True)
        #     # 假設 interact/song.wav 存在
        #     play_wav_to_device("interact_audio/song.wav", self.DEVICE_ID, on_done=None)
        #     await self.handle_commands(message)
        #     return  # 處理完畢，不繼續檢查其他條件
        #
        # # 2. 偵測年齡相關
        # if re.search('|'.join(re.escape(k.lower()) for k in age_keywords), message_content_lower):
        #     print("偵測到年齡相關訊息。")
        #     stop_playback()
        #     os.makedirs("interact", exist_ok=True)
        #     # 假設 interact/age.wav 存在
        #     play_wav_to_device("interact_audio/age.wav", self.DEVICE_ID, on_done=None)
        #     await self.handle_commands(message)
        #     return  # 處理完畢，不繼續檢查其他條件
        #
        # # 3. 偵測介紹類
        # if re.search('|'.join(re.escape(k.lower()) for k in introduce_keywords), message_content_lower):
        #     print("偵測到介紹類訊息。")
        #     stop_playback()
        #     os.makedirs("interact", exist_ok=True)
        #     # 假設 interact/introduce.wav 存在
        #     play_wav_to_device("interact_audio/introduce.wav", self.DEVICE_ID, on_done=None)
        #     await self.handle_commands(message)
        #     return  # 處理完畢，不繼續檢查其他條件
        #
        # # 打招呼
        # if re.search('|'.join(re.escape(k.lower()) for k in greeting_keywords), message_content_lower):
        #     random_greet_id = random.randint(1, 6)
        #     random_name_id = random.randint(1, 3)
        #     stop_playback()
        #     await process_and_combine_audio(message.author.name,random_greet_id,random_name_id)
        #     play_wav_to_device(f"combined_audio/combined_audio_{message.author.name}_{random_greet_id}_{random_name_id}.wav",self.DEVICE_ID,on_done=None)
        #     await self.handle_commands(message)
        #     return
        # label = await llm_classify_message(message.content)
        # label = classify_message_sync(message.content)

        label, reply = classify_message_sync(message.content)

        # 撥放語音（如果 AI 給了）
        if reply:
            # 在聊天室中以主播身分回覆訊息
            await message.channel.send(f"@{message.author.name} {reply}")

        if label == "greet":
            random_greet_id = random.randint(1, 6)
            random_name_id = random.randint(1, 3)
            stop_playback()
            await process_and_combine_audio(message.author.name, random_greet_id, random_name_id)
            play_wav_to_device(
                f"combined_audio/combined_audio_{message.author.name}_{random_greet_id}_{random_name_id}.wav",
                self.DEVICE_ID,
                on_done=None
            )

        elif label == "song":
            stop_playback()
            play_wav_to_device("interact_audio/song.wav", self.DEVICE_ID, on_done=None)

        elif label == "age":
            stop_playback()
            play_wav_to_device("interact_audio/age.wav", self.DEVICE_ID, on_done=None)

        elif label == "introduce":
            stop_playback()
            play_wav_to_device("interact_audio/introduce.wav", self.DEVICE_ID, on_done=None)

        elif label == "stop":
            if self.is_playing_news and self.news_timer:
                self.news_timer.stop()
                self.is_playing_news = False
                self.sched.clear_queue()

        elif label == "news":
            self.news_timer = QTimer()
            self.is_playing_news = True

            def play_news():
                title, script, idx = random.choice(self.NewsPool)
                self.sched.enqueue(title, script, idx)

            self.news_timer.timeout.connect(play_news)
            self.news_timer.start(3 * 60 * 1000)
            self.news_timer.timeout.emit()

        elif label == "nod":
            self.vts.nod_head()

        elif label == "shake":
            self.vts.shake_head()

        elif label == "happy":
            self.vts.happy()

        elif label == "confuse":
            self.vts.confuse()

        elif label == "despise":
            self.vts.despise()

        # 若有任何行為就 return
        if label != "none":
            await self.handle_commands(message)
            return

