from voicevox import Client
import asyncio
import os


async def generate_greeting_audio(name: str, speaker_id: int,name_id: int ):
    """
    根據指定的名字和說話者 ID 生成「[名字]リーホォー」的語音檔案。

    Args:
        name (str): 要嵌入問候語中的名字。
        speaker_id (int): VOICEVOX 說話者的風格 ID。
    """
    # 定義包含帶有名字的問候短句陣列
    # 陣列索引通常從 0 開始，但如果你想讓 name_id 從 1 開始對應，
    # 可以讓第 0 個元素為空或作為預設值。
    name_greetings = [
        "",  # 佔位符，讓 name_id 1 對應到 index 1
        f"{name}さんリーホォー",  # name_id = 1
        f"{name}さんジャッばァボエ？",  # name_id = 2 (台語：[名字]吃飽沒？)
        f"シォンベーティァシャミッ、{name}さん"
    ]

    # 選擇對應的問候短句並格式化插入名字
    # 由於陣列索引從 0 開始，所以使用 name_id - 1
    selected_greeting_template = name_greetings[name_id]
    text_to_synthesize = selected_greeting_template

    async with Client() as client:
        # 組合問候語
        # text_to_synthesize = f"{name}さんリーホォー"

        try:
            # 建立音訊查詢
            audio_query = await client.create_audio_query(
                text=text_to_synthesize,
                speaker=speaker_id
            )

            # 確保輸出目錄存在
            output_dir = "name_audio"
            os.makedirs(output_dir, exist_ok=True)

            # 生成檔案名稱
            output_filename = os.path.join(output_dir, f"{name}{name_id}.wav")

            # 執行語音合成並寫入 WAV 文件
            with open(output_filename, "wb") as f:
                f.write(await audio_query.synthesis(speaker=speaker_id))

            print(f"成功生成 '{text_to_synthesize}' 的語音檔案：{output_filename}")

        except Exception as e:
            print(f"生成語音時發生錯誤：{e}")


async def get_speakers():
    """
    獲取並列印所有可用的 VOICEVOX 說話者及其風格 ID。
    """
    async with Client() as client:
        speakers = await client.fetch_speakers()
        print("可用的說話者和風格：")
        for speaker in speakers:
            print(f"說話者名稱: {speaker.name}, UUID: {speaker.uuid}")
            for style in speaker.styles:
                print(f"  - 風格名稱: {style.name}, ID: {style.id}")
        print("-" * 30)


if __name__ == "__main__":
    # 先獲取可用的說話者列表，以便選擇 speaker_id
    asyncio.run(get_speakers())

    # 範例使用：生成「Johnリーホォー」的語音，使用 ID 2 的聲線
    # 請根據上方 get_speakers 的輸出選擇一個實際存在的 ID
    # asyncio.run(generate_greeting_audio("John", 2))

    # 您也可以嘗試用不同的名字和聲線
    # asyncio.run(generate_greeting_audio("Mary", 0))
    # asyncio.run(generate_greeting_audio("Bob", 5))