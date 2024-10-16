from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionFactory
from src.game_logic.services.general import Services


async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_services(session: AsyncSession = Depends(get_session)):
    return Services(session)
