from fastapi import APIRouter, Depends, HTTPException

from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.schemas.inventory_schemas import (
    InventoryResponse,
    StackBase,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "", response_model=InventoryResponse, dependencies=[Depends(get_current_user)]
)
async def get_inventory(
    current_user=Depends(get_current_user), services=Depends(get_services)
):
    """Получить инвентарь текущего пользователя"""
    return await services.inventory_service.get_inventory(current_user.id)


@router.post(
    "/add", response_model=InventoryResponse, dependencies=[Depends(get_current_user)]
)
async def add_items(
    items: list[StackBase],
    current_user=Depends(get_current_user),
    services=Depends(get_services),
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
    current_user=Depends(get_current_user),
    services=Depends(get_services),
):
    """Удалить предметы из инвентаря"""
    try:
        return await services.inventory_service.remove_items(current_user.id, items)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get(
    "/has-item/{item_id}", response_model=bool, dependencies=[Depends(get_current_user)]
)
async def check_has_item(
    item_id: int,
    quantity: int = 1,
    current_user=Depends(get_current_user),
    services=Depends(get_services),
):
    """Проверить наличие предмета в инвентаре"""
    return await services.inventory_service.has_item(current_user.id, item_id, quantity)
