import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.responses import JSONResponse

from auth.models import User
from auth.user_service import get_current_user
from cache.client import cache_service
from config.game_settings import time_add_one_energy, energy_per_time, energy
from src.game_logic.energy.router import energy_service
from topics.energy import EnergyTopic

router = APIRouter(prefix="/ws/energy", tags=["websocket router"])


@router.websocket("/")
async def energy_websocket(websocket: WebSocket,
                           user: User = Depends(get_current_user)):
    await websocket.accept()  # Принимаем подключение WebSocket

    # Создаем или получаем топик для данного пользователя
    user_key = f"energy_topic:{user.id}"
    topic = await cache_service.redis.get(user_key)

    if topic is None:
        topic = EnergyTopic(user_id=user.id)
        await cache_service.redis.set(
            user_key, json.dumps({"subscribers": []})
        )  # Создаем новый топик в Redis

    else:
        topic = EnergyTopic(user_id=user.id)  # Восстанавливаем топик из Redis

    topic.subscribe(websocket)  # Подписываем пользователя на топик

    try:
        await send_initial_energy(
            websocket, user.id
        )  # Отправляем текущее состояние энергии
        asyncio.create_task(
            energy_update_periodically(websocket, user.id, topic)
        )  # Запускаем обновление энергии

        while True:
            data = await websocket.receive_json()  # Ждем входящие сообщения от клиента
            await handle_client_message(
                data, user.id, topic, websocket
            )  # Обрабатываем сообщение клиента

    except WebSocketDisconnect:
        topic.unsubscribe(websocket)  # Отписываем пользователя при отключении
        await cache_service.redis.set(
            user_key, json.dumps({"subscribers": list(topic.subscribers)})
        )  # Обновляем подписчиков в Redis
        print(f"Client {user.id} disconnected from energy topic")
    except Exception as e:
        await handle_error(websocket, str(e))  # Обработка ошибок
    finally:
        await websocket.close()  # Закрываем WebSocket соединение


async def send_initial_energy(websocket: WebSocket, user_id: int):
    """Отправляет текущее состояние энергии пользователю при подключении."""
    energy_data = await energy_service.get_energy(user_id)
    await websocket.send_json({"event": "energy_update", "energy": energy_data.amount})


async def energy_update_periodically(
    websocket: WebSocket, user_id: int, topic: EnergyTopic
):
    """Обновляет энергию пользователя каждые time_add_one_energy секунд."""
    while True:
        await asyncio.sleep(time_add_one_energy)  # Ждем указанное время
        updated_energy = await energy_service.update_energy(
            user_id=user_id, amount=energy_per_time[time_add_one_energy]
        )  # Прибавляем единицу энергии

        topic.publish(
            {"event": "energy_update", "energy": updated_energy.amount}
        )  # Уведомляем подписчиков

        if updated_energy.amount >= energy["energy_max"]:
            await handle_max_energy(websocket, topic)  # Обработка достижения максимума
            break


async def handle_max_energy(websocket: WebSocket, topic: EnergyTopic):
    """Обрабатывает случай, когда энергия достигает максимума."""
    topic.unsubscribe(websocket)  # Отписка при достижении максимума
    await websocket.send_json(
        {
            "event": "max_energy",
            "message": "Энергия достигла максимума, вы отписаны от обновлений.",
        }
    )


async def handle_client_message(data: dict, user_id: int,
                                topic: EnergyTopic, websocket: WebSocket):
    """Обрабатывает входящие сообщения от клиента."""
    if data.get("event") == "battle_start":
        battle_cost = data.get("cost", 0)
        updated_energy = await energy_service.update_energy(
            user_id=user_id, amount=-battle_cost
        )

        if isinstance(updated_energy, JSONResponse):
            await websocket.send_json(
                {"event": "error", "message": updated_energy.content["message"]}
            )
        else:
            topic.publish(
                {"event": "energy_update", "energy": updated_energy.amount}
            )  # Уведомление подписчиков

            if updated_energy.amount >= energy["energy_max"]:
                await handle_max_energy(
                    websocket, topic
                )  # Обработка достижения максимума


async def handle_error(websocket: WebSocket, message: str):
    """Отправляет сообщение об ошибке пользователю."""
    await websocket.send_json({"event": "error", "message": message})
    print(f"Error in websocket connection: {message}")
