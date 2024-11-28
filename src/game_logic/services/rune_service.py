from fastapi import HTTPException
from sqlalchemy import select, delete

from src.game_logic.models.models import Rune
from src.game_logic.services.service import Service


class RuneService(Service):
    async def get_all(self):
        result = await self.session.execute(select(Rune))
        races = result.unique().scalars().all()
        return races

    async def get_by_id(self, id: int):
        result = await self.session.execute(select(Rune).where(Rune.id == id))
        race = result.scalars().first()
        if not race:
            raise HTTPException(400, detail='No race with such id')
        return race

    async def delete_by_id(self, id: int):
        result = await self.session.execute(delete(Rune).where(Rune.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No race with such id')
        await self.session.commit()
        return result
