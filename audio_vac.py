import sounddevice as sd, soundfile as sf, threading

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

    def _worker():
        sd.play(data, fs, device=dev_idx, blocking=True)
        on_done()

    threading.Thread(target=_worker, daemon=True).start()
