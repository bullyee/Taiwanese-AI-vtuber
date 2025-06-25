import sounddevice as sd, soundfile as sf, threading

# 初始化當前的音訊串流為 None
current_stream = None
# 初始化一個鎖，用於同步對音訊串流的訪問
stream_lock = threading.Lock()

def stop_playback():
    """
            停止當前正在播放的音檔並釋放相關資源。
            """
    global current_stream, stream_lock  # 宣告要使用全域變數
    with stream_lock:
        if current_stream and current_stream.active:
            print("手動停止播放並釋放資源...")
            current_stream.stop()  # 停止串流
            current_stream.close()  # 關閉串流，釋放音訊裝置
            current_stream = None  # 清除對串流的引用
            sd.stop()
        else:
            print("目前沒有音檔正在播放。")


def list_devices():
    for i, d in enumerate(sd.query_devices()):
        if d['max_output_channels'] > 0:
            host = sd.query_hostapis(d['hostapi'])['name']
            print(f"{i:2d}: {d['name']}  [{host}]")

def _resolve_device(name_or_id, host_preference=("Windows WASAPI", "MME", "DirectSound")):
    """把 'Line 1 ...' 或 (name, host) 轉成唯一 device index"""
    if isinstance(name_or_id, int):
        return name_or_id                    # 已是索引
    if isinstance(name_or_id, tuple):
        # 明確 (name, host) 二元組
        name, host = name_or_id
        for i, d in enumerate(sd.query_devices()):
            if d['name'] == name and sd.query_hostapis(d['hostapi'])['name'] == host:
                return i
        raise ValueError(f"沒有找到裝置 {name} @ {host}")
    # 字串 → 找到第一個符合 host_preference
    matches = [ (i, sd.query_hostapis(d['hostapi'])['name'])
                for i, d in enumerate(sd.query_devices())
                if d['name'] == name_or_id and d['max_output_channels']>0 ]
    for pref in host_preference:
        for idx, host in matches:
            if host == pref:
                return idx
    if matches:
        return matches[0][0]                 # 退而取第一個
    raise ValueError(f"找不到裝置 {name_or_id}")

def play_wav_to_device(wav_path, device_name, on_done=lambda:None):

    data, fs = sf.read(wav_path, dtype='float32')
    if data.ndim == 1:
        data = data[:, None].repeat(2, axis=1)

    dev_idx = _resolve_device(device_name)

    # def _worker():
    #     sd.play(data, fs, device=dev_idx, blocking=True)
    #     on_done()
    def _worker():
        global current_stream, stream_lock  # 宣告要使用全域變數
        with stream_lock:
            # 如果有舊的串流存在且仍在播放，先停止並關閉它
            if current_stream and current_stream.active:
                print("停止之前的播放並釋放資源...")
                current_stream.stop()
                current_stream.close()
                # 這裡不需要清除 current_stream，因為稍後會賦予新的串流
            # 創建新的音訊輸出串流
            try:
                # 使用 sd.OutputStream 來更精細地控制音訊輸出
                stream = sd.OutputStream(
                    samplerate=fs,
                    channels=data.shape[1],  # 聲道數 (1 或 2)
                    dtype=data.dtype,
                    device=dev_idx
                )
                current_stream = stream  # 將新的串流賦值給全域變數
                stream.start()  # 啟動串流

                # 將音訊數據寫入串流
                stream.write(data)
                sd.play(data, fs, device=dev_idx, blocking=True)
            except Exception as e:
                print(f"播放音檔時發生錯誤: {e}")
            finally:
                on_done()  # 播放完成或發生錯誤後執行回調函數

    threading.Thread(target=_worker, daemon=True).start()