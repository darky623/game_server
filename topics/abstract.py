from abc import ABC, abstractmethod

from fastapi import WebSocket


class Topic(ABC):
    def __init__(self, topic_id: str):
        self.topic_id = topic_id
        self.subscribers: set[WebSocket] = set()

    @abstractmethod
    def publish(self, message: dict):
        """Публикация сообщения в топик."""
        pass

    def subscribe(self, websocket: WebSocket):
        """Подписка на топик."""
        self.subscribers.add(websocket)

    def unsubscribe(self, websocket: WebSocket):
        """Отписка от топика."""
        self.subscribers.discard(websocket)


