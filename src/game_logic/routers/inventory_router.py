from fastapi import APIRouter, Depends, HTTPException

from auth import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.schemas.inventory_schemas import (
    InventoryResponse,
    StackBase,
)
from src.game_logic.services.general import Services

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "", dependencies=[Depends(get_current_user)]
)
async def get_inventory(
        current_user: User = Depends(get_current_user),
        services: Services = Depends(get_services)

):
    """Получить инвентарь текущего пользователя"""
    return await services.inventory_service.get_inventory(current_user.id)


@router.post(
    "/add", response_model=InventoryResponse, dependencies=[Depends(get_current_user)]
)
async def add_items(
        items: list[StackBase],
        current_user: User = Depends(get_current_user),
        services: Services = Depends(get_services),
):
    """Добавить предметы в инвентарь"""
    try:
        return await services.inventory_service.add_items_to_inventory(
            current_user.id, items
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.post(
    "/remove",
    response_model=InventoryResponse,
    dependencies=[Depends(get_current_user)],
)
async def remove_items(
        items: list[StackBase],
        current_user: User = Depends(get_current_user),
        services: Services = Depends(get_services),
):
    """Удалить предметы из инвентаря"""
    try:
        return await services.inventory_service.remove_items(current_user.id, items)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.post(
    "/has-item/{item_id}", response_model=bool, dependencies=[Depends(get_current_user)]
)
async def check_has_item(
        items_to_check: list[StackBase],
        current_user: User = Depends(get_current_user),
        services: Services = Depends(get_services),
):
    """Проверить наличие предмета в инвентаре"""
    return await services.inventory_service.has_items(current_user.id, items_to_check)


@router.post("/transfer")
async def transfer_item(
        to_user_id: int,
        item_id: int,
        quantity: int,
        current_user: User = Depends(get_current_user),
        services: Services = Depends(get_services)
):
    await services.inventory_service.transfer_item(current_user.id, to_user_id, item_id, quantity)
    return {"message": "Item transferred successfully"}
