import asyncio, json, websockets, uuid, pathlib, threading, queue

WS_URL      = "ws://127.0.0.1:8001"
PLUGIN_NAME = "VAC_Control_Python"
DEVELOPER   = "Austin"
TOKEN_FILE  = pathlib.Path("vts_token.txt")

class VTSClient:
    def __init__(self, queue_size=100):
        self.q: "queue.Queue[str]" = queue.Queue(queue_size)
        self.thread = threading.Thread(target=self._run, daemon=True, name="VTSClient")
        self.thread.start()

    # ---------- 對外 API ----------
    def trigger_hotkey(self, hotkey_id: str):
        """把 Hotkey ID 丟進佇列；GUI 執行緒呼叫也安全"""
        try:
            print("enqueued a new hotkey trigger")
            self.q.put_nowait(hotkey_id)
        except queue.Full:
            print("VTS queue full! Hotkey dropped:", hotkey_id)

    # ---------- 內部 ----------
    async def _ws_send(self, ws, msg_type, data=None):
        msg = {
            "apiName":"VTubeStudioPublicAPI",
            "apiVersion":"1.0",
            "messageType":msg_type,
            "requestID":str(uuid.uuid4()),
            "data": data or {}
        }
        await ws.send(json.dumps(msg))
        return json.loads(await ws.recv())

    async def _producer(self):
        async with websockets.connect(WS_URL) as ws:
            # 1) 取得／讀取 token
            if not TOKEN_FILE.exists():
                token_rsp = await self._ws_send(ws, "AuthenticationTokenRequest", {
                    "pluginName": PLUGIN_NAME,
                    "pluginDeveloper": DEVELOPER
                })
                TOKEN_FILE.write_text(token_rsp["data"]["authenticationToken"])

            token = TOKEN_FILE.read_text().strip()

            # 2) 驗證
            auth_rsp = await self._ws_send(ws, "AuthenticationRequest", {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": DEVELOPER,
                "authenticationToken": token
            })
            if not auth_rsp["data"]["authenticated"]:
                raise RuntimeError("❌ VTS Authentication failed!")

            print("✅ VTS authenticated. Ready for hotkeys.")

            # 3) 持續監聽佇列 → 送 HotkeyTriggerRequest
            while True:
                hotkey = await asyncio.get_event_loop().run_in_executor(None, self.q.get)
                await self._ws_send(ws, "HotkeyTriggerRequest",
                                    {"hotkeyID": hotkey})

    def _run(self):
        asyncio.run(self._producer())
