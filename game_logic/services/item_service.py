from fastapi import HTTPException
from sqlalchemy import select, delete

from game_logic.models import Item
from .service import Service


class ItemService(Service):
    async def get_all(self):
        result = await self.session.execute(select(Item))
        items = result.unique().scalars().all()
        return items

    async def get_by_id(self, id: int):
        result = await self.session.execute(select(Item).where(Item.id == id))
        item = result.scalars().first()
        if not item:
            raise HTTPException(400, detail='No item with such id')
        return item

    async def get_by_ids(self, item_ids: list[int]):
        if not item_ids: return []
        result = await self.session.execute(select(Item).where(Item.id.in_(item_ids)))
        return result.scalars().all()

    async def delete_by_id(self, id: int):
        result = await self.session.execute(delete(Item).where(Item.id == id))
        if result.rowcount == 0:
            raise HTTPException(400, detail='No item with such id')
        await self.session.commit()
        return result
