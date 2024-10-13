from fastapi import APIRouter, Depends
from starlette import status

from auth.models import User
from auth.user_service import get_current_user

from clan.clan_service import ClanService
from clan.schemas import (
    ClanSchemaCreate,
    ClanSchema,
    ClanSchemaUpdate,
    SubscribeToClanSchema,
)
from database import AsyncSessionFactory
from typing import List

router = APIRouter(prefix="/subscribe", tags=["subscribe_to_clan"])
clan_service = ClanService(AsyncSessionFactory)


@router.get(
    "/incoming_requests",
    response_model=List[SubscribeToClanSchema],
    status_code=status.HTTP_200_OK,
)
async def get_incoming_requests(user: User = Depends(get_current_user)):
    """
    Текущий пользователь получает список приглашений в клан.

    Args:
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        JsonResponse: Список приглашений.

    Raises:
        HTTPException: Возникает, если клан не найден.
        HTTPException: Возникает, если у пользователя нет доступа до просмотра заявок.
    """
    return await clan_service.get_clan_incoming_requests(user.id)


@router.post(
    "/{clan_id}/{accept_user_id}/confirm_request",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def confirm_request(
    clan_id: int, accept_user_id: int, user: User = Depends(get_current_user)
):
    """
    Текущий пользователь подтверждает запрос на вступление в клан от другого пользователя.

    Args:
        clan_id (int): ID запроса.
        accept_user_id (int): ID пользователя, который отправил запрос на вступление.
        user (User): Пользователь, подтверждающий запрос.

    Raises:
        HTTPException: Если запрос не найден.
    """
    return await clan_service.confirm_request(clan_id, accept_user_id, user.id)


@router.post(
    "/{clan_id}/{invited_user_id}/invite", response_model=SubscribeToClanSchema
)
async def invite_to_clan(
    clan_id: int, invited_user_id: int, user: User = Depends(get_current_user)
):
    """
    Текущий пользователь создает приглашение в клан для другого пользователя.

    Args:
        clan_id (int): ID клана.
        invited_user_id (int): ID пользователя, которому отправляется приглашение.
        user (User): Пользователь, подписывающийся на клан.


    Returns:
        SubscribeToClanSchema: Подписка на клан.

    Raises:
        HTTPException: Если клан не найден.
    """
    return await clan_service.invite_to_clan(clan_id, invited_user_id, user.id)


@router.get("/all", response_model=List[SubscribeToClanSchema])
async def get_all_comings_to_clans(user: User = Depends(get_current_user)):
    """
    Текущий пользователь получает список приглашений.

    Args:
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        JsonResponse: Список приглашений.
    """
    return await clan_service.get_all_comings_to_clans(user.id)


@router.post("/{clan_id}/accept_invite", response_model=SubscribeToClanSchema)
async def subscribe_to_clan(clan_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь принимает приглашение в клан. Подписывается на клан.

    Args:
        clan_id (int): ID клана.
        user (User): Пользователь, подписывающийся на клан.

    Returns:
        SubscribeToClanSchema: Подписка на клан.

    Raises:
        HTTPException: Если клан не найден.
    """
    return await clan_service.accept_invite(clan_id, user.id)


@router.get("/{clan_id}/members", response_model=List[SubscribeToClanSchema])
async def get_clan_members(clan_id: int) -> List[User]:
    """
    Получение списка членов клана.

    Args:
        clan_id (int): ID клана.

    Returns:
        List[User]: Список членов клана.

    Raises:
        HTTPException: Если клан не найден.
    """
    return await clan_service.get_clan_members(clan_id)


@router.post("/{clan_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_clan(clan_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь пытается отписаться от клана.

    Args:
        clan_id (int): ID клана.
        user (User): Пользователь, отписывающийся от клана.

    Raises:
        HTTPException: Если клан не найден или пользователь не подписан на клан.
    """
    return await clan_service.leave_clan(clan_id, user.id)


@router.post("/{clan_id}/{user_id}/{new_role}", response_model=SubscribeToClanSchema)
async def change_member_role(
    clan_id: int,
    user_id: int,
    new_role: str,
    current_user: User = Depends(get_current_user),
):
    """
    Текущий пользователь изменяет роли члена клана.

    Args:
        clan_id (int): ID клана.
        user_id (int): ID пользователя, чья роль изменяется.
        new_role (str): Новая роль.
        current_user (User): Пользователь, изменяющий роль.

    Returns:
        SubscribeToClanSchema: Данные о пользователе с обновленной ролью.

    Raises:
        HTTPException:
            - Если клан не найден.
            - Если пользователь не найден в клане.
            - Если текущий пользователь не имеет прав на изменение роли.
            - Если указана неверная роль.
            - Если достигнут лимит на количество пользователей с определенной ролью.
    """
    return await clan_service.change_member_role(
        clan_id, user_id, new_role, current_user.id
    )


@router.post(
    "/request_to_join/{clan_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=SubscribeToClanSchema,
)
async def request_to_clan(clan_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь отправляет запрос на вступление в публичный клан.

    Args:
        clan_id (int): ID клана.
        user (User): Пользователь, отправляющий запрос.

    Raises:
        HTTPException: Если клан не найден.
    """
    return await clan_service.request_to_clan(clan_id, user.id)


@router.post("/{clan_id}/decline_invite", status_code=status.HTTP_200_OK)
async def decline_invite(clan_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь отклоняет приглашение в клан направленное ему из клана.

    Args:
        clan_id (int): ID клана.
        user (User): Текущий аутентифицированный пользователь.

    Returns:
        JsonResponse: Сообщение об отклонении приглашения.

    Raises:
        HTTPException: Возникает, если приглашение не найдено.
    """
    return await clan_service.decline_invite(clan_id, user.id)
