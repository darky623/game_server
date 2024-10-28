import asyncio
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from sqlalchemy.orm import Session

from config.database import AsyncSessionFactory
from config.deps import get_services
from src.game_logic.energy.models import Energy
from websoket.ws_connection_manager import ConnectionManager

router = APIRouter(prefix='/ws/chat', tags=['chat websocket router'])

manager = ConnectionManager()
energy_service = EnergyService(AsyncSessionFactory)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, session: Session = Depends(get_services)):
    await manager.connect(websocket)
    try:
        energy_obj = session.query(Energy).filter(Energy.user_id == user_id).first()
        if energy_obj is None:
            await websocket.send_text("Error: User not found")
            await websocket.close()
            return

        while energy_obj.current_energy < energy_obj.max_energy:
            await asyncio.sleep(60)
            energy_obj.current_energy += 1
            session.commit()  # Сохраняем изменения в БД
            await manager.send_personal_message(str(energy_obj.current_energy), websocket)

        await websocket.send_text(f"Max energy reached! Disconnecting.")
        await websocket.close()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        session.close()


async def publish_energy_update(user_id: int, energy: EnergyPydantic, db: AsyncSession):
    channel = f"energy:{user_id}"
    await redis_connection.publish(channel, energy.json())
    # Обновление в базе данных (важно делать это после публикации, чтобы избежать рассогласования)
    energy_db = await db.query(Energy).filter(Energy.user_id == user_id).first()
    if energy_db:
        energy_db.amount = energy.amount
        energy_db.last_updated = datetime.utcnow()
        await db.commit()
