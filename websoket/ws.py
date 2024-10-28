from fastapi import WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from fastapi.responses import JSONResponse

from websoket.topics.energy import EnergyTopic

router = APIRouter(prefix='/ws/energy/', tags=['websocket router'])

topics = {}  # Словарь для хранения топиков (topic_id: Topic)


@router.websocket("/{topic_id}")
async def energy_endpoint(websocket: WebSocket, topic_id: str):
    try:
        topic = topics.get(topic_id)
        if topic is None:
            raise HTTPException(status_code=404, detail="Topic not found")
        await topic.subscribe(websocket)
        try:
            while True:
                # Здесь можно добавить обработку сообщений от клиента
                data = await websocket.receive_json()
                # Обработка данных от клиента
                # Например, обработка начала боя:
                if data.get("event") == "battle_start" and isinstance(topic, EnergyTopic):
                    battle_cost = data.get("cost", 0)  # Количество энергии, которое снимается за бой
                    topic.update_energy(-battle_cost)

        except WebSocketDisconnect:
            topic.unsubscribe(websocket)
            print(f"Client disconnected from topic {topic_id}")
    except HTTPException as e:
        await websocket.send_json({"error": e.detail})
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        print(f"Error processing websocket connection: {e}")
    finally:
        await websocket.close()


# Пример создания топика:
topics["energy_123"] = EnergyTopic(user_id=123)
