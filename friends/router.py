from fastapi import APIRouter, status

from auth.models import User
from chat.router import chat_service
from database import AsyncSessionFactory
from friend_service import FriendService
from friends.schemas import RequestToFriendCreate

router = APIRouter(prefix="/friends", tags=["Друзья"])

friend_service = FriendService(AsyncSessionFactory)


@router.post("/send_request", status_code=status.HTTP_201_CREATED)
async def send_friend_request(request: RequestToFriendCreate):
    """Отправить заявку в друзья"""
    return await friend_service.send_friend_request(request)


@router.put("/accept/{request_id}", status_code=status.HTTP_200_OK)
async def accept_friend_request(request_id: int):
    """Принять заявку в друзья"""
    return await friend_service.accept_friend_request(request_id)


@router.put("/decline/{request_id}", status_code=status.HTTP_200_OK)
async def decline_friend_request(request_id: int):
    """Отклонить заявку в друзья"""
    return await friend_service.decline_friend_request(request_id)


@router.delete("/cancel/{request_id}", status_code=status.HTTP_200_OK)
async def cancel_friend_request(request_id: int):
    """Отменить заявку в друзья"""
    return await friend_service.cancel_friend_request(request_id)


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(friend_id: int):
    """Удалить из друзей"""
    return await friend_service.remove_friend(friend_id)


@router.get(
    "/list/{user_id}", response_model=list[User], status_code=status.HTTP_200_OK
)
async def get_friends_list(user_id: int):
    """Получить список друзей"""
    return await friend_service.get_friends_list(user_id)


@router.post("/create_chat", status_code=status.HTTP_201_CREATED)
async def create_private_chat(user_id: int, friend_id: int):
    """Создать приватный чат между пользователем и его другом"""
    return await chat_service.create_chat(user_id, friend_id)
