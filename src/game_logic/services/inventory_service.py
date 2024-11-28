from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.game_logic.models.inventory_models import Inventory, Item, Stack
from src.game_logic.schemas.inventory_schemas import (
    InventoryResponse,
    StackBase,
    StackCreate,
)
from src.game_logic.services.service import Service
from cache.client import cache_service

class InventoryService(Service):
    async def _create_inventory(self, user_id: int) -> Inventory:
        inventory = Inventory(user_id=user_id)
        self.session.add(inventory)
        try:
            await self.session.commit()
            await self.session.refresh(inventory)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create inventory")
        return inventory

    async def _get_inventory_with_items(self, user_id: int) -> Inventory:
        """Вспомогательный метод для получения инвентаря с загруженными предметами"""
        try:
            inventory_query = await self.session.execute(
                select(Inventory)
                .options(joinedload(Inventory.stacks).joinedload(Stack.item))
                .where(Inventory.user_id == user_id)
            )
            return inventory_query.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Error fetching inventory")

    async def get_inventory(self, user_id: int) -> InventoryResponse:
        try:
            inventory = await self._get_inventory_with_items(user_id)
            if not inventory:
                inventory = await self._create_inventory(user_id)

            if inventory is None:
                raise HTTPException(status_code=404, detail="Inventory not found")
            
            # Ensure all relationships are loaded
            await self.session.refresh(inventory, ["stacks"])
            for stack in inventory.stacks:
                await self.session.refresh(stack, ["item"])
            
            # Create response after ensuring all data is loaded
            return InventoryResponse.model_validate(inventory)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Database error")

    async def add_items_to_inventory(
        self, user_id: int, items_to_add: list[StackBase]
    ) -> InventoryResponse:
        try:
            # Get inventory with related stacks and items
            inventory = await self._get_inventory_with_items(user_id)

            if not inventory:
                inventory = await self._create_inventory(user_id)

            # Add items to inventory
            for stack_data in items_to_add:
                # Получаем информацию о предмете
                item_result = await self.session.execute(
                    select(Item).where(Item.id == stack_data.item_id)
                )
                item = item_result.scalar_one_or_none()

                if not item:
                    raise HTTPException(
                        status_code=404, detail=f"Item {stack_data.item_id} not found"
                    )

                # Проверяем максимальный размер стека для предмета
                if stack_data.quantity <= 0:
                    raise HTTPException(
                        status_code=400, detail="Quantity must be greater than 0"
                    )

                if item.is_stacked:
                    # Для стакающихся предметов
                    existing_stack = next(
                        (stack for stack in inventory.stacks if stack.item_id == item.id),
                        None,
                    )

                    if existing_stack:
                        # Увеличиваем количество в существующем стеке
                        existing_stack.quantity += stack_data.quantity
                    else:
                        # Создаем новый стек
                        new_stack = Stack(
                            inventory_id=inventory.id,
                            item_id=item.id,
                            quantity=stack_data.quantity,
                        )
                        inventory.stacks.append(new_stack)
                else:
                    # Для не стакающихся предметов
                    for _ in range(stack_data.quantity):
                        new_stack = Stack(
                            inventory_id=inventory.id,
                            item_id=item.id,
                            quantity=1,
                        )
                        inventory.stacks.append(new_stack)

            await self.session.commit()
            return await self.get_inventory(user_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to add items to inventory")

    async def remove_items(self, user_id: int, items_to_remove: List[StackBase]) -> InventoryResponse:
        """Удаление предметов из инвентаря"""
        if not items_to_remove:
            return await self.get_inventory(user_id)

        try:
            inventory = await self._get_inventory_with_items(user_id)
            if not inventory:
                raise HTTPException(status_code=404, detail="Inventory not found")

            for stack_data in items_to_remove:
                # Получаем информацию о предмете
                item_result = await self.session.execute(
                    select(Item).where(Item.id == stack_data.item_id)
                )
                item = item_result.scalar_one_or_none()
                
                if not item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item {stack_data.item_id} not found"
                    )

                # Находим все стеки с нужным предметом
                matching_stacks = [
                    stack for stack in inventory.stacks 
                    if stack.item_id == stack_data.item_id
                ]

                if not matching_stacks:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item {stack_data.item_id} not found in inventory"
                    )

                remaining_to_remove = stack_data.quantity
                stacks_to_delete = []

                if item.is_stacked:
                    # Для стакающихся предметов
                    # Удаляем предметы из стеков
                    for stack in matching_stacks:
                        if stack.quantity <= remaining_to_remove:
                            remaining_to_remove -= stack.quantity
                            stacks_to_delete.append(stack)
                        else:
                            stack.quantity -= remaining_to_remove
                            remaining_to_remove = 0
                            break
                else:
                    # Для не стакающихся предметов
                    # Просто удаляем нужное количество стеков
                    if len(matching_stacks) < stack_data.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Not enough items of type {stack_data.item_id}"
                        )
                    stacks_to_delete = matching_stacks[:stack_data.quantity]
                    remaining_to_remove = 0

                if remaining_to_remove > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough items of type {stack_data.item_id}"
                    )

                # Удаляем пустые стеки
                for stack in stacks_to_delete:
                    inventory.stacks.remove(stack)
                    await self.session.delete(stack)

            await self.session.commit()
            return await self.get_inventory(user_id)
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to remove items from inventory")

    async def has_items(self, user_id: int, items_to_check: list[StackBase]) -> bool:
        """Проверка наличия предметов в инвентаре"""
        if not items_to_check:
            return False
        try:
            inventory = await self._get_inventory_with_items(user_id)
            if not inventory:
                return False

            for required_stack in items_to_check:
                total_quantity = sum(
                    stack.quantity
                    for stack in inventory.stacks
                    if stack.item_id == required_stack.item_id
                )
                
                if total_quantity < required_stack.quantity:
                    return False

            return True
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Error checking inventory items")

    async def get_item_quantity(self, user_id: int, item_id: int) -> int:
        """Получение количества определенного предмета в инвентаре"""
        try:
            inventory = await self._get_inventory_with_items(user_id)
            if not inventory:
                return 0

            return sum(
                stack.quantity
                for stack in inventory.stacks
                if stack.item_id == item_id
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Error getting item quantity")