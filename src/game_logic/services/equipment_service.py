from fastapi import HTTPException
from sqlalchemy import select, and_

from src.game_logic.models import Character, SummandParams, MultiplierParams
from src.game_logic.models.inventory_models import Item
from src.game_logic.schemas.inventory_schemas import StackBase
from src.game_logic.services.inventory_service import InventoryService
from src.game_logic.services.service import Service


class EquipmentService(Service):
    inventory_service: InventoryService

    def __init__(self, session):
        super().__init__(session)
        self.inventory_service = InventoryService(session)

    async def equip_item(self, user_id: int, character_id: int, item_id: int) -> dict:
        try:
            character = await self.session.execute(
                select(Character)
                .where(
                    and_(Character.id == character_id,
                         Character.user_id == user_id)
                )
            )
            character = character.scalars().first()
            item = await self.session.execute(
                select(Item)
                .where(Item.id == item_id))

            item = item.scalars().first()

            # Проверка на наличие у персонажа такого итема
            if item in character.items:
                return {"success": False, "message": "Character already has this item equipped"}

            if not character or not item:
                return {"success": False, "message": "Character or item not found"}

            # Проверка на наличие у пользователя данного итема
            if not await self.inventory_service.has_items(user_id, [StackBase(item_id=item_id, quantity=1)]):
                return {"success": False, "message": "Not enough items in inventory"}

            if item.tier == 0:
                return {"success": False, "message": "This item cannot be equipped"}

            if item.tier < 1 or item.tier > 5:
                return {"success": False, "message": "Invalid item tier"}

            # Добавляем предмет к персонажу
            character.items.append(item)

            # Обновляем параметры персонажа
            if item.summand_params:
                # if not character.summand_params:
                #     character.summand_params = SummandParams()
                character.summand_params += item.summand_params

            if item.multiplier_params:
                # if not character.multiplier_params:
                #     character.multiplier_params = MultiplierParams()
                character.multiplier_params *= item.multiplier_params

            # Удаляем предмет из инвентаря
            await self.inventory_service.remove_items(user_id, [StackBase(item_id=item_id, quantity=1)])

            await self.session.commit()
            return {"success": True, "message": "Item equipped successfully"}
        except Exception as e:
            await self.session.rollback()
            print(f"Error occurred while equipping item: {e}")
            return {"success": False, "message": "An error occurred"}

    async def unequip_item(self, character_id: int, user_id: int, item_id: int) -> dict:
        # try:

        character = await self.session.execute(
            select(Character)
            .where(
                and_(Character.id == character_id,
                     Character.user_id == user_id)
            )
        )
        character = character.scalars().first()
        item = await self.session.execute(
            select(Item)
            .where(Item.id == item_id))

        item = item.scalars().first()

        if not character or not item:
            return {"success": False, "message": "Character or item not found"}
        # Проверка на наличие у героя данного итема
        if item not in character.items:
            return {"success": False, "message": "Item is not equipped"}

        # Удаляем предмет из персонажа
        if item.summand_params:
            character.summand_params -= item.summand_params
        if item.multiplier_params:
            character.multiplier_params /= item.multiplier_params

        character.items.remove(item)
        # Добавляем предмет в инвентарь
        await self.inventory_service.add_items_to_inventory(
            user_id, [StackBase(item_id=item_id, quantity=1)]
        )

        await self.session.commit()
        return {"success": True, "message": "Item unequipped successfully"}
        # except Exception as e:
        #     await self.session.rollback()
        #     print(f"Error occurred while unequipping item: {e}")
        #     return {"success": False, "message": "An error occurred"}
