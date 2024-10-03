from fastapi import APIRouter, Depends
from starlette import status

from auth.models import User
from auth.user_service import get_current_user

from clan.clan_service import ClanService
from clan.schemas import ClanSchemaCreate, ClanSchema, ClanSchemaUpdate, SubscribeToClanSchema
from database import AsyncSessionFactory
from typing import List

router = APIRouter(prefix='/clan')
clan_service = ClanService(AsyncSessionFactory)


@router.post('/create', response_model=ClanSchemaCreate)
async def create_clan(clan: ClanSchemaCreate,
                      user: User = Depends(get_current_user)):
    """
        Создание нового клана.

        Args:
            clan (ClanSchemaCreate): Данные для создания клана.
            user (User): Текущий аутентифицированный пользователь.

        Returns:
            ClanSchema: Созданный клан.

        Raises:
            HTTPException: Если возникла ошибка при создании клана.
        """
    return await clan_service.create_clan(clan, user)


@router.get('/{clan_id}', response_model=ClanSchema)
async def get_clan(
        clan_id: int,
):
    """
    Получение информации о клане по его ID.

    Args:
        clan_id (int): ID клана.

    Returns:
        ClanSchema: Информация о клане.

    Raises:
        HTTPException: Если клан не найден.
    """
    return await clan_service.get_clan_by_id(clan_id)


@router.get('/', response_model=List[ClanSchema])
async def list_clans(
        skip: int = 0,
        limit: int = 100
):
    """
    Получение списка публичных кланов с пагинацией.

    Args:
        skip (int): Количество пропускаемых записей.
        limit (int): Максимальное количество возвращаемых записей.

    Returns:
        List[ClanSchema]: Список кланов.
    """
    return await clan_service.get_public_clans(skip, limit)


@router.put('/{clan_id}', response_model=ClanSchema)
async def update_clan(
        clan_id: int,
        clan_update: ClanSchemaUpdate,
        current_user: User = Depends(get_current_user)
):
    """
    Обновление информации о клане.

    Args:
        clan_id (int): ID клана для обновления.
        clan_update (ClanSchemaUpdate): Данные для обновления клана.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        ClanSchema: Обновленная информация о клане.

    Raises:
        HTTPException: Если клан не найден или пользователь не имеет прав на обновление.
    """
    return await clan_service.edit_clan(clan_id, clan_update, current_user.id)


@router.delete('/{clan_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_clan(
        clan_id: int,
        current_user: User = Depends(get_current_user)
):
    """
    Удаление клана(может только глава).

    Args:
        clan_id (int): ID клана для удаления.
        current_user (User): Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: Если клан не найден или пользователь не имеет прав на удаление.
    """
    await clan_service.delete_clan(clan_id, current_user)


@router.get('/{clan_id}/members', response_model=List[User])
async def get_clan_members(clan_id: int):
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


@router.post('/{clan_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
async def leave_clan(clan_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь пытается отписаться от клана.

    Args:
        clan_id (int): ID клана.
        user (User): Пользователь, отписывающийся от клана.

    Raises:
        HTTPException: Если клан не найден или пользователь не подписан на клан.
    """
    await clan_service.leave_clan(clan_id, user.id)


@router.post('/{clan_id}/{user_id}/{new_role}', response_model=SubscribeToClanSchema)
async def change_member_role(clan_id: int,
                             user_id: int,
                             new_role: str,
                             current_user: User = Depends(get_current_user)):
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
    return await clan_service.change_member_role(clan_id, user_id, new_role, current_user.id)


@router.post('{clan_id}/request_to_join', status_code=status.HTTP_204_NO_CONTENT)
async def request_to_clan(clan_id: int,
                          user: User = Depends(get_current_user)):
    """
    Текущий пользователь отправляет запрос на вступление в публичный клан.

    Args:
        clan_id (int): ID клана.
        user (User): Пользователь, отправляющий запрос.

    Raises:
        HTTPException: Если клан не найден.
    """
    await clan_service.request_to_clan(clan_id, user.id)


@router.post('{clan_id}/confirm_request', status_code=status.HTTP_204_NO_CONTENT)
async def confirm_request(clan_id: int,
                          accept_user_id: int,
                          user: User = Depends(get_current_user)):
    """
    Текущий пользователь подтверждает запрос на вступление в клан от другого пользователя.

    Args:
        clan_id (int): ID запроса.
        accept_user_id (int): ID пользователя, который отправил запрос на вступление.
        user (User): Пользователь, подтверждающий запрос.

    Raises:
        HTTPException: Если запрос не найден.
    """
    await clan_service.confirm_request(clan_id, accept_user_id, user.id)


@router.post('{clan_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
async def leave_clan(clan_id, user: User = Depends(get_current_user)):
    """
    Позволяет текущему пользователю выходить из клана.

    Args:
        clan_id (int): ID клана.
        user (User): Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: Если пользователь не найден в клане.
    """
    await clan_service.leave_clan(clan_id, user.id)


@router.post('{clan_id}/kick', status_code=status.HTTP_204_NO_CONTENT)
async def kick_from_clan(clan_id: int, kick_user_id: int, user: User = Depends(get_current_user)):
    """
    Текущий пользователь Исключает подписчика из клана.

    Args:
        clan_id (int): ID клана.
        kick_user_id (int): ID пользователя, которого нужно исключить.
        user (User): Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: Если пользователь не найден в клане.
    """
    await clan_service.kick_from_clan(clan_id, kick_user_id, user.id)


@router.post("{clan_id}/decline_invite", status_code=status.HTTP_204_NO_CONTENT)
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
    await clan_service.decline_invite(clan_id, user.id)




