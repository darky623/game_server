from fastapi import APIRouter, status, Depends

from auth.models import User
from auth.user_service import get_current_user

from database import AsyncSessionFactory
from friends.friend_service import FriendService
from friends.schemas import RequestToFriendCreate, RequestToFriendUpdate

router = APIRouter(prefix="/friends", tags=["Friends"])

friend_service = FriendService(AsyncSessionFactory)


@router.post(
    "/send_request/{friend_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=RequestToFriendCreate,
)
async def send_friend_request(friend_id: int, user: User = Depends(get_current_user)):
    """Отправить заявку в друзья"""
    return await friend_service.send_friend_request(friend_id, user.id)


@router.put(
    "/accept_friendship",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    response_model=RequestToFriendUpdate
)
async def accept_friend_request(
    request: RequestToFriendUpdate, user: User = Depends(get_current_user)
):
    """Принять заявку в друзья"""
    return await friend_service.accept_friend_request(request, user.id)


@router.delete(
    "/cancel/{request_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
async def cancel_friend_request(request_id: int, user: User = Depends(get_current_user)):
    """Отменить заявку в друзья"""
    return await friend_service.cancel_friend_request(request_id, user.id)


@router.delete(
    "/{friend_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_user)],
)
async def remove_friend(friend_id: int, user: User = Depends(get_current_user)):
    """Удалить из друзей"""
    return await friend_service.remove_friend(friend_id, user.id)


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
async def get_coming_friend_requests(user: User = Depends(get_current_user)):
    """Получить входящие заявки в друзья"""
    incoming_requests = await friend_service.get_coming_friend_requests(user.id)
    return incoming_requests


@router.get("/coming_requests", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def get_all_incoming_requests(user: User = Depends(get_current_user)):
    """Получить исходящие заявки в друзья"""
    incoming_requests = await friend_service.get_all_incoming_requests(user.id)
    return incoming_requests
