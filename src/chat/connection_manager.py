from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self):
        self.chat_websocket_lists: dict[int, list[WebSocket]] = {}

    async def connect_to_chat(self, chat_id: int, websocket: WebSocket):
        await websocket.accept()
        self.chat_websocket_lists.setdefault(chat_id, []).append(websocket)

    async def disconnect(self, chat_id, websocket: WebSocket):
        self.chat_websocket_lists[chat_id].remove(websocket)

    async def send_personal_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, chat_id: int):
        for websocket in self.chat_websocket_lists.get(chat_id, []):
            await websocket.send_json(message)
