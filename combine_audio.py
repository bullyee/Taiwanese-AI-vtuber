import asyncio

from pydub import AudioSegment

from voicevox_tts import generate_greeting_audio


def combine_audio_files(file1_path, file2_path, output_path):
    """
    將兩個音檔合併成一個。

    Args:
        file1_path (str): 第一個音檔的路徑。
        file2_path (str): 第二個音檔的路徑。
        output_path (str): 合成後音檔的儲存路徑。
    """
    try:
        # 載入第一個音檔
        audio1 = AudioSegment.from_file(file1_path)
        print(f"成功載入 {file1_path}")

        # 載入第二個音檔
        audio2 = AudioSegment.from_file(file2_path)
        print(f"成功載入 {file2_path}")

        # 合併音檔 (audio2 會接在 audio1 後面)
        combined_audio = audio1 + audio2
        print("音檔合併成功！")

        # 儲存合併後的音檔
        # pydub 會根據副檔名自動判斷格式 (例如 .mp3, .wav, .flac 等)
        combined_audio.export(output_path, format="mp3")
        print(f"合併後的音檔已儲存至 {output_path}")

    except Exception as e:
        print(f"合併音檔時發生錯誤: {e}")

async def process_and_combine_audio(person_name: str, greet_id: int, name_id: int):
    """
    根據提供的參數生成語音並合併音檔。
    Args:
        person_name (str): 用於生成語音的人名 (例如 "John")。
        greet_id (int): 對應 greet_audio/greetX.wav 的數字 ID (例如 1)。
        name_id (int): 對應 name_audio/PersonNameY.wav 的數字 ID (例如 2)。
    """
    print(f"\n--- 開始處理 {person_name}, greet_id={greet_id}, name_id={name_id} ---")

    # 此處speakerID為聲線
    await generate_greeting_audio(person_name, 2,name_id),
    # 構建檔案路徑
    # 假設 name_audio 的檔案命名格式是 {person_name}_{name_id}.wav
    audio_file1 = f"name_audio/{person_name}{name_id}.wav"
    # 假設 greet_audio 的檔案命名格式是 greet{greet_id}.wav
    audio_file2 = f"greet_audio/greet{greet_id}.wav"
    # 輸出檔案命名格式可以自定義，這裡使用 combined_audio_{person_name}_{greet_id}_{name_id}.wav
    output_combined_file = f"combined_audio/combined_audio_{person_name}_{greet_id}_{name_id}.wav"

    # 確保輸出目錄存在
    import os
    os.makedirs("combined_audio", exist_ok=True)

    # 呼叫合併音檔函式
    combine_audio_files(audio_file1, audio_file2, output_combined_file)
    print(f"--- 完成處理 {person_name}, greet_id={greet_id}, name_id={name_id} ---\n")

# --- 使用範例 ---
if __name__ == "__main__":
#     asyncio.run(generate_greeting_audio("John", 2))
#     # 確保你有 audio1.mp3 和 audio2.mp3 在相同的目錄下，或者提供完整的路徑
#     # 這裡假設音檔格式是 MP3，pydub 也支援其他格式如 .wav, .flac 等
      audio_file1 = "04.wav"  # 替換成你的第一個音檔路徑
      audio_file2 = "03.wav"  # 替換成你的第二個音檔路徑
      output_combined_file = "interact_audio/introduce.wav" # 合成後的新音檔路徑
#
      combine_audio_files(audio_file1, audio_file2, output_combined_file)