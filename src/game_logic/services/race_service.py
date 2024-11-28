from fastapi import HTTPException
from sqlalchemy import select, delete

from src.game_logic.models.models import Race
from .service import Service


class RaceService(Service):
    async def get_all(self):
        result = await self.session.execute(select(Race))
        races = result.unique().scalars().all()
        return races

    async def get_by_id(self, id: int):
        result = await self.session.execute(select(Race).where(Race.id == id))
        race = result.scalars().first()
        if not race:
            raise HTTPException(400, detail='No race with such id')
        return race

    async def delete_by_id(self, id: int):
        result = await self.session.execute(delete(Race).where(Race.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No race with such id')
        await self.session.commit()
        return result
