from abc import ABC, abstractmethod

from starlette.websockets import WebSocket


class Topic(ABC):
    def __init__(self, topic_id: str):
        self.topic_id = topic_id
        self.subscribers: dict[int, set[WebSocket]] = {}

    @abstractmethod
    def publish(self, message: dict):
        """Публикация сообщения в топик."""
        pass

    def subscribe(self, websocket: WebSocket):
        """Подписка на топик."""
        self.subscribers.setdefault(websocket, set()).add(websocket)

    def unsubscribe(self, websocket: WebSocket):
        """Отписка от топика."""
        self.subscribers.pop(websocket)


