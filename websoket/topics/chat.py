import asyncio

from starlette.websockets import WebSocket

from websoket.topics.abstract import Topic


class ChatTopic(Topic):
    def __init__(self, topic_id: str):
        super().__init__(topic_id)

    def publish(self, message: dict):
        """Отправляет сообщение всем подписчикам."""
        for ws in self.subscribers:
            asyncio.create_task(ws.send_json(message))

    # def personal_publish(self, message: dict, websocket: WebSocket):
    #     asyncio.create_task(websocket.send_json(message))


