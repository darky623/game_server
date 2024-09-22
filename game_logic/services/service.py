from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import Base


class Service:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj: Base):
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_all(self):
        raise NotImplemented

    async def get(self, **kwargs):
        raise NotImplemented

    async def get_by_id(self, id: int):
        raise NotImplemented

    async def delete_by_id(self, id: int):
        raise NotImplemented
