import asyncio

from topics.abstract import Topic


class EnergyTopic(Topic):
    def __init__(self, user_id: int):  # Топик привязан к пользователю
        super().__init__(f"energy_{user_id}")  # Используем user_id в topic_id
        self.user_id = user_id

    def publish(self, message: dict):
        """Отправляет сообщение всем подписчикам, обновляет энергию."""
        for ws in self.subscribers:
            asyncio.create_task(ws.send_json(message))
