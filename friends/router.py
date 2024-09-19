from fastapi import APIRouter, status, Depends

from auth.models import User
from auth.user_service import get_current_user
from chat.router import chat_service
from database import AsyncSessionFactory
from friends.friend_service import FriendService, create_private_chat
from friends.schemas import RequestToFriendCreate

router = APIRouter(prefix="/friends", tags=["Друзья"])

friend_service = FriendService(AsyncSessionFactory)


@router.post(
    "/send_request",
    status_code=status.HTTP_201_CREATED,
    response_model=RequestToFriendCreate,
    dependencies=[Depends(get_current_user)],
)
async def send_friend_request(request: RequestToFriendCreate):
    """Отправить заявку в друзья"""
    return await friend_service.send_friend_request(request)


@router.put(
    "/accept/{request_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def accept_friend_request(request_id: int):
    """Принять заявку в друзья"""
    return await friend_service.accept_friend_request(request_id)


@router.delete(
    "/cancel/{request_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def cancel_friend_request(request_id: int):
    """Отменить заявку в друзья"""
    return await friend_service.cancel_friend_request(request_id)


@router.delete(
    "/{friend_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
async def remove_friend(friend_id: int):
    """Удалить из друзей"""
    return await friend_service.remove_friend(friend_id)


@router.get(
    "/list/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def get_friends_list(user_id: int):
    """Получить список друзей"""
    return await friend_service.get_friends_list(user_id)


@router.get(
    "/incoming_requests",
    status_code=status.HTTP_200_OK,
    response_model=list[RequestToFriendCreate],
    dependencies=[Depends(get_current_user)],
)
async def get_incoming_friend_requests(current_user: User = Depends(get_current_user)):
    """Получить входящие заявки в друзья"""
    incoming_requests = await friend_service.get_incoming_friend_requests(current_user.id)
    print(f"Incoming requests returned: {incoming_requests}")  # Отладочный вывод
    return incoming_requests


@router.post(
    "/create_chat",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
async def create_chat(user_id: int, friend_id: int):
    """Создать приватный чат между пользователем и его другом"""
    return await create_private_chat(user_id, friend_id)
    # return await chat_service.create_chat(user_id, friend_id)
