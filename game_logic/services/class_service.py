from fastapi import HTTPException

from game_logic.services.service import Service
from game_logic.models import CharacterClass, CharacterSubclass
from sqlalchemy import select


class ClassService(Service):
    async def get_all(self):
        result = await self.session.execute(select(CharacterClass))
        classes = result.unique().scalars().all()
        return classes

    async def add_subclass(self, character_class: CharacterClass, subclass: CharacterSubclass):
        character_class.subclasses.append(subclass)
        await self.session.commit()
        await self.session.refresh(subclass)
        return subclass

    async def get_subclasses(self, class_id: int):
        character_class = await self.get_by_id(class_id)
        if not character_class:
            raise HTTPException(400, detail='No class with such id')
        return character_class.subclasses


    async def get_by_id(self, class_id: int):
        result = await self.session.execute(select(CharacterClass).where(CharacterClass.id == class_id))
        character_class = result.scalars().first()
        if not character_class:
            raise HTTPException(400, detail='No class with such id')
        return character_class

    async def delete_subclass_by_id(self, class_id: int, subclass_id: int):
        result = await self.session.execute(
            select(CharacterSubclass).where(
                CharacterSubclass.character_class_id == class_id,
                CharacterSubclass.id == subclass_id)
        )
        subclass = result.scalars().first()
        if not subclass:
            raise HTTPException(400, detail='No such subclass in this class')
        await self.session.delete(subclass)
        await self.session.commit()
        return True