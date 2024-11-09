from fastapi import APIRouter, Depends, HTTPException
from chat.schemas import AddChatSchema, ChatSchema
from auth.models import User
from auth.user_service import get_current_user
from chat.chat_service import ChatService
from database import AsyncSessionFactory
from typing import Optional

router = APIRouter(prefix='/chat', tags=['chat'])
chat_service = ChatService(AsyncSessionFactory)


@router.post('', response_model=ChatSchema)
async def create_chat(add_chat: AddChatSchema = Depends,
                      user: User = Depends(get_current_user)):
    chat = await chat_service.create_chat(add_chat)
    return chat


@router.get('/{chat_id}/messages')
async def get_last_messages(chat_id: int,
                            quantity: Optional[int] = 15,
                            user: User = Depends(get_current_user)):
    if await chat_service.check_chat_member(chat_id, user):
        messages = await chat_service.get_last_messages(chat_id, quantity)
        response = [message.serialize() for message in messages]
        return response
    raise HTTPException(400, 'You are not allowed to get messages from this chat')


@router.get('')
async def get_all_allowed_chats(user: User = Depends(get_current_user)):
    general_chat = await chat_service.get_general_chat()
    result = [general_chat.id]
    for chat in user.chats:
        if chat:
            result.append(chat.id)
    return {
        'allowed_chat_ids': set(result)
    }


@router.delete('/{chat_id}/{message_id}')
async def delete_message(chat_id: int, message_id: int, user: User = Depends(get_current_user)):
    try:
        await chat_service.delete_message(chat_id, message_id, user)
        return {'message': 'Message deleted'}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# @router.get('/{chat_id}')
# async def get_chat_info(chat_id: int,
#                         user: User = Depends(get_current_user)):
#     if not await chat_service.check_chat_member(chat_id, user):
#         raise HTTPException(403, detail='You are not allowed to see this chat info')
#     chat = await chat_service.get_chat(chat_id)
#     return chat
