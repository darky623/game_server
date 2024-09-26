from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionFactory
from game_logic.services.general import Services


async def get_session(commit_on_close=True) -> AsyncSession:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            if commit_on_close:
                await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_services(session: AsyncSession = Depends(get_session)):
    return Services(session)
