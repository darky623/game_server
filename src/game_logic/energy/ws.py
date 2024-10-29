from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.responses import JSONResponse

from auth.models import User
from auth.user_service import get_current_user
from src.game_logic.energy.router import energy_service

from websoket.topics.energy import EnergyTopic

router = APIRouter(prefix='/ws/energy', tags=['websocket router'])

energy_topics = {}  # Словарь для хранения топиков (topic_id: Topic)


@router.websocket("")
async def energy_websocket(websocket: WebSocket, user: User = Depends(get_current_user)):
    await websocket.accept()

    # Создаем или получаем топик для данного пользователя
    if user.id not in energy_topics:
        energy_topics[user.id] = EnergyTopic(user_id=user.id)

    topic = energy_topics[user.id]
    topic.subscribe(websocket)

    try:
        # Отправка текущего состояния энергии при подключении
        energy_data = await energy_service.get_energy(user.id)
        await websocket.send_json(
            {"event": "energy_update", "energy": energy_data.amount}
        )

        while True:
            # Здесь можно обрабатывать сообщения от клиента, если это необходимо
            data = await websocket.receive_json()
            # Например, можно добавить логику для начала боя:
            if data.get("event") == "battle_start":
                battle_cost = data.get("cost", 0)
                updated_energy = await energy_service.update_energy(
                    user_id=user.id, amount=-battle_cost
                )
                if isinstance(updated_energy, JSONResponse):
                    await websocket.send_json(
                        {"event": "error", "message": updated_energy.content["message"]}
                    )
                else:
                    # Отправка обновленного состояния энергии
                    await topic.publish(
                        {"event": "energy_update", "energy": updated_energy.amount}
                    )
                    # Проверка на максимальное значение энергии
                    if updated_energy.amount >= 100:
                        topic.unsubscribe(websocket)
                        await websocket.send_json(
                            {
                                "event": "max_energy",
                                "message": "Энергия достигла максимума, вы отписаны от обновлений.",
                            }
                        )
                        break
    except WebSocketDisconnect:
        topic.unsubscribe(websocket)
        print(f"Client {user.id} disconnected from energy topic.")
    except Exception as e:
        await websocket.send_json({"event": "error", "message": str(e)})
        print(f"Error in websocket connection: {e}")
    finally:
        await websocket.close()

