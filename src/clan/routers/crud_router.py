from fastapi import APIRouter, Depends
from starlette import status

from auth.models import User
from auth.user_service import get_current_user

from src.clan.clan_service import ClanService
from src.clan.schemas import (
    ClanSchemaCreate,
    ClanSchema,
    ClanSchemaUpdate,
)
from config.database import AsyncSessionFactory
from typing import List

router = APIRouter(prefix="/clan", tags=["clan"])
clan_service = ClanService(AsyncSessionFactory)


@router.post("/create", response_model=ClanSchemaCreate)
async def create_clan(clan: ClanSchemaCreate, user: User = Depends(get_current_user)):
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
    return await clan_service.create_clan(clan, user.id)


@router.get("/{clan_id}", response_model=ClanSchema)
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


@router.get("", response_model=List[ClanSchema])
async def list_clans(skip: int = 0, limit: int = 100):
    """
    Получение списка публичных кланов с пагинацией.

    Args:
        skip (int): Количество пропускаемых записей.
        limit (int): Максимальное количество возвращаемых записей.

    Returns:
        List[ClanSchema]: Список кланов.
    """
    return await clan_service.get_public_clans(skip, limit)


@router.put("/{clan_id}", response_model=ClanSchema)
async def update_clan(
    clan_id: int,
    clan_update: ClanSchemaUpdate,
    current_user: User = Depends(get_current_user),
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


@router.delete("/{clan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clan(clan_id: int, current_user: User = Depends(get_current_user)):
    """
    Удаление клана(может только глава).

    Args:
        clan_id (int): ID клана для удаления.
        current_user (User): Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: Если клан не найден или пользователь не имеет прав на удаление.
    """
    return await clan_service.delete_clan(clan_id, current_user.id)


@router.post("/{clan_id}/{kick_user_id}/kick", status_code=status.HTTP_200_OK)
async def kick_from_clan(
    clan_id: int, kick_user_id: int, user: User = Depends(get_current_user)
):
    """
    Текущий пользователь Исключает подписчика из клана.

    Args:
        clan_id (int): ID клана.
        kick_user_id (int): ID пользователя, которого нужно исключить.
        user (User): Текущий аутентифицированный пользователь.

    Raises:
        HTTPException: Если пользователь не найден в клане.
    """
    return await clan_service.kick_from_clan(clan_id, kick_user_id, user.id)
