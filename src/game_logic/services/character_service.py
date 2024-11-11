from fastapi import HTTPException
from sqlalchemy import select, delete

from src.game_logic.models.models import Character
from .service import Service
from ..schemas.character_schema import CharacterSchema


class CharacterService(Service):
    async def get_by_user_id(self, user_id: int) -> list[CharacterSchema]:
        result = await self.session.execute(select(Character).where(Character.user_id == user_id))
        characters = result.unique().scalars().all()
        return CharacterSchema.many_from_orm(characters)

    async def delete_by_id(self, id: int):
        result = await self.session.execute(delete(Character).where(Character.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No character with such id')
        await self.session.commit()
        return result

    async def delete_by_id_by_user(self, id: int, user_id: int):
        result = await self.session.execute(
            select(Character).where(Character.id == id, Character.user_id == user_id)
        )
        character = result.scalars().first()
        if not character:
            raise HTTPException(400, detail='No character with such id or you are not owner')
        await self.session.delete(character)
        await self.session.commit()

    async def get_by_id(self, id: int):
        result = await self.session.execute(select(Character).where(Character.id == id))
        character = result.scalars().first()
        if not character:
            raise HTTPException(400, detail='No character with such id')
        return character

    async def get_many_by_ids(self, ids: list[int]):
        result = await self.session.execute(select(Character).where(Character.id.in_(ids)))
        characters = result.unique().scalars().all()
        return characters

    async def update(self, id: int, character_data: Character):
        result = await self.session.execute(select(Character).where(Character.id == id))
        character = result.scalars().first()

        if not character:
            raise HTTPException(404, detail="Character not found")

        character.name = character_data.name
        character.avatar = character_data.avatar
        character.class_id = character_data.class_id
        character.subclass_id = character_data.subclass_id
        character.race_id = character_data.race_id
        character.character_type = character_data.character_type
        character.summand_params_id = character_data.summand_params_id
        character.multiplier_params_id = character_data.multiplier_params_id
        character.stardom = character_data.stardom
        character.level = character_data.level

        character.items = character_data.items
        character.abilities = character_data.abilities
        character.power = character_data.power

        self.session.add(character)
        await self.session.commit()

        return character
