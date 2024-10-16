from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from auth.models import User
from auth.user_service import websocket_authentication
from src.chat.router import chat_service
from datetime import datetime

from src.chat.connection_manager import ChatConnectionManager

router = APIRouter(prefix='/ws/chat', tags=['chat websocket router'])

manager = ChatConnectionManager()


@router.websocket('/{chat_id}')
async def chat_websocket(websocket: WebSocket,
                         chat_id: int,
                         user: User = Depends(websocket_authentication)
):
    try:
        if not user:
            await websocket.send_json(str({
                'error': 'Token is invalid'
            }))
            await websocket.close(code=1008)
            return
        if not await chat_service.check_chat_member(chat_id, user):
            await websocket.send_json(str({
                'error': 'You are not allowed to join this chat'
            }))
            await websocket.close(code=1008)
            return

        await manager.connect_to_chat(chat_id, websocket)
        await manager.send_personal_json({
            'text': 'You are successfully connected to chat!'
        }, websocket)

        while True:
            data = await websocket.receive_json()
            text = data.get('text')
            if not text:
                await websocket.send_json(
                    {
                        'error': 'It is not a valid message',
                    })
                continue
            timestamp = datetime.now()
            await chat_service.add_message(text=text,
                                           user_id=user.id,
                                           chat_id=chat_id,
                                           timestamp=timestamp)
            await manager.broadcast({
                'username': user.username,
                'user_id': user.id,
                'text': text,
                'timestamp': timestamp.isoformat()
            }, chat_id)

    except WebSocketDisconnect:
        await manager.disconnect(chat_id, websocket)
