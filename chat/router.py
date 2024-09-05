from fastapi import APIRouter, Depends
from chat.schemas import AddChatSchema, ChatSchema
from auth.models import User
from auth.user_service import get_current_user
from chat.chat_service import ChatService
from database import AsyncSessionFactory

router = APIRouter(prefix='/chat')
chat_service = ChatService(AsyncSessionFactory)


@router.post('', response_model=ChatSchema)
async def create_chat(add_chat: AddChatSchema = Depends,
                      user: User = Depends(get_current_user)):
    chat = await chat_service.create_chat(add_chat)
    return chat


