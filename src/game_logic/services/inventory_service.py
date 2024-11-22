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
        inventory_query = await self.session.execute(
            select(Inventory)
            .options(joinedload(Inventory.stacks).joinedload(Stack.item))
            .where(Inventory.user_id == user_id)
        )
        return inventory_query.unique().scalar_one_or_none()

    async def get_inventory(self, user_id: int) -> InventoryResponse:
        try:
            inventory = await self._get_inventory_with_items(user_id)
            if not inventory:
                inventory = await self._create_inventory(user_id)

            if inventory is None:
                raise HTTPException(status_code=404, detail="Inventory not found")

            return InventoryResponse.from_orm(inventory)
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
                # Get item info
                item_result = await self.session.execute(
                    select(Item).where(Item.id == stack_data.item_id)
                )
                item = item_result.scalar_one_or_none()

                if not item:
                    raise HTTPException(
                        status_code=404, detail=f"Item {stack_data.item_id} not found"
                    )

                if item.is_stacked:
                    # Для стакающихся предметов ищем существующий стек
                    existing_stack = next(
                        (stack for stack in inventory.stacks if stack.item_id == item.id),
                        None,
                    )

                    if existing_stack:
                        # Если стек существует, увеличиваем количество
                        existing_stack.quantity += stack_data.quantity
                    else:
                        # Если стека нет, создаем новый
                        new_stack = Stack(
                            inventory_id=inventory.id,
                            item_id=item.id,
                            quantity=stack_data.quantity,
                        )
                        inventory.stacks.append(new_stack)
                else:
                    # Для не стакающихся предметов создаем отдельные стеки
                    for _ in range(stack_data.quantity):
                        new_stack = Stack(
                            inventory_id=inventory.id, item_id=item.id, quantity=1
                        )
                        inventory.stacks.append(new_stack)

            await self.session.commit()
            await self.session.refresh(inventory)
            return InventoryResponse.from_orm(inventory)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to transfer item")

    async def remove_items(
        self, user_id: int, items_to_remove: list[StackBase]
    ) -> InventoryResponse:
        try:
            # Get inventory and stacks
            inventory = await self._get_inventory_with_items(user_id)

            if not inventory:
                raise HTTPException(status_code=404, detail="Inventory not found")

            # Remove items
            for stack_data in items_to_remove:
                # Find stack with this item
                existing_stack = next(
                    (
                        stack
                        for stack in inventory.stacks
                        if stack.item_id == stack_data.item_id
                    ),
                    None,
                )

                if not existing_stack:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item {stack_data.item_id} not found in inventory",
                    )

                if existing_stack.quantity < stack_data.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough items in stack. Have {existing_stack.quantity}, need {stack_data.quantity}",
                    )

                # Remove items from stack
                existing_stack.quantity -= stack_data.quantity
                if existing_stack.quantity == 0:
                    inventory.stacks.remove(existing_stack)
                    await self.session.delete(existing_stack)

            await self.session.commit()
            await self.session.refresh(inventory)
            return InventoryResponse.from_orm(inventory)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to transfer item")

    async def has_items(self, user_id: int, items_to_check: list[StackCreate]) -> bool:
        """
        Функция проверяет наличие всех предметов в нужном количестве.
        Возвращает False, если хотя бы один предмет отсутствует или его недостаточно.
        Возвращает True только если все предметы найдены в достаточном количестве.
        Проверка количества выполняется только если стек существует.
        """
        inventory = await self._get_inventory_with_items(user_id)

        if not inventory:
            return False

        for stack_data in items_to_check:
            existing_stack = next(
                (
                    stack
                    for stack in inventory.stacks
                    if stack.item_id == stack_data.item_id
                ),
                None,
            )

            if not existing_stack or existing_stack.quantity < stack_data.quantity:
                return False

        return True

    async def transfer_item(self, from_user_id: int, to_user_id: int, item_id: int, quantity: int) -> None:
        """
        Передает предмет из инвентаря одного пользователя в инвентарь другого.

        :param from_user_id: ID пользователя, отдающего предмет
        :param to_user_id: ID пользователя, получающего предмет
        :param item_id: ID передаваемого предмета
        :param quantity: Количество передаваемых предметов
        """
        try:
            # Получаем инвентари обоих пользователей

            from_inventory = await self._get_inventory_with_items(from_user_id)
            to_inventory = await self._get_inventory_with_items(to_user_id)

            if not from_inventory or not to_inventory:
                raise HTTPException(status_code=404, detail="Inventory not found")

            # Находим стек с нужным предметом в инвентаре отправителя
            from_stack = next((stack for stack in from_inventory.stacks if stack.item_id == item_id), None)

            if not from_stack:
                raise HTTPException(status_code=404, detail="Item not found in sender's inventory")

            if from_stack.quantity < quantity:
                raise HTTPException(status_code=400, detail="Not enough items in sender's inventory")

            # Проверяем, можно ли передавать этот предмет
            if from_stack.item.is_personal:
                raise HTTPException(status_code=400, detail="This item cannot be transferred")

            # Уменьшаем количество предметов в инвентаре отправителя
            from_stack.quantity -= quantity

            # Если стек стал пустым, удаляем его
            if from_stack.quantity == 0:
                from_inventory.stacks.remove(from_stack)
                await self.session.delete(from_stack)

            # Находим или создаем стек в инвентаре получателя
            to_stack = next((stack for stack in to_inventory.stacks if stack.item_id == item_id), None)

            if to_stack:
                to_stack.quantity += quantity
            else:
                new_stack = Stack(inventory_id=to_inventory.id, item_id=item_id, quantity=quantity)
                to_inventory.stacks.append(new_stack)
                self.session.add(new_stack)

            # Сохраняем изменения
            await self.session.commit()

            await self.session.refresh(from_inventory)
            await self.session.refresh(to_inventory)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to transfer item")

