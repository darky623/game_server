from fastapi import HTTPException
from sqlalchemy import select
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
        await self.session.commit()
        await self.session.refresh(inventory)
        return inventory

    async def get_inventory(self, user_id: int) -> InventoryResponse:
        # Query the database for the user's inventory
        inventory = await self.session.execute(
            select(Inventory)
            .options(joinedload(Inventory.stacks).joinedload(Stack.item))
            .where(Inventory.user_id == user_id)
        )
        # Create inventory if not exists
        if not inventory:
            inventory = await self._create_inventory(user_id)

        inventory = inventory.unique().scalar_one_or_none()

        return InventoryResponse.from_orm(inventory)

    async def add_items_to_inventory(
        self, user_id: int, items_to_add: list[StackBase]
    ) -> InventoryResponse:
        # Get inventory with related stacks and items
        inventory_result = await self.session.execute(
            select(Inventory)
            .options(joinedload(Inventory.stacks).joinedload(Stack.item))
            .where(Inventory.user_id == user_id)
        )
        inventory = inventory_result.unique().scalar_one_or_none()

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

    async def remove_items(
        self, user_id: int, items_to_remove: list[StackBase]
    ) -> InventoryResponse:
        # Get inventory and stacks
        inventory_query = await self.session.execute(
            select(Inventory)
            .options(joinedload(Inventory.stacks))
            .where(Inventory.user_id == user_id)
        )
        inventory = inventory_query.unique().scalar_one_or_none()

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

    async def has_items(self, user_id: int, items_to_check: list[StackCreate]) -> bool:
        # Check if user has enough of specific item
        inventory_query = await self.session.execute(
            select(Inventory)
            .options(joinedload(Inventory.stacks))
            .where(Inventory.user_id == user_id)
        )
        inventory = inventory_query.unique().scalar_one_or_none()

        if not inventory:
            return False
        for stack_data in items_to_check:
            # Find stack with this item
            existing_stack = next(
                (
                    stack
                    for stack in inventory.stacks
                    if stack.item_id == stack_data.item_id
                ),
                None,
            )

            if existing_stack:
                return True

            if existing_stack.quantity >= stack_data.quantity:
                return True
        return False
