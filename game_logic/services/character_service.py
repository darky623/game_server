from fastapi import HTTPException
from sqlalchemy import select, delete

from game_logic.models.models import Character
from .service import Service


class CharacterService(Service):
    async def get_by_user_id(self, user_id: int):
        result = await self.session.execute(select(Character).where(Character.user_id == user_id))
        characters = result.unique().scalars().all()
        return characters

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
