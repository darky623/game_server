import asyncio

from websoket.topics.abstract import Topic


class EnergyTopic(Topic):
    def __init__(self, user_id: int):  # Топик привязан к пользователю
        super().__init__(f"energy_{user_id}")  # Используем user_id в topic_id
        self.user_id = user_id
        self.energy_level = 0  # Начальный уровень энергии
        self.max_energy = 100

    def publish(self, message: dict):
        """Отправляет сообщение всем подписчикам, обновляет энергию."""
        for ws in self.subscribers:
            asyncio.create_task(ws.send_json(message))

    def update_energy(self, delta: int):
        """Обновляет уровень энергии пользователя."""
        self.energy_level = max(0, min(self.energy_level + delta, self.max_energy))  # Защита от переполнения
        self.publish({"event": "energy_update", "energy": self.energy_level})
