import asyncio
from auth.models import *
from game_logic.models import *
from chat.models import *
from database import engine, Base
from routes import create_archetypes


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # await create_archetypes()


if __name__ == '__main__':
    asyncio.run(init_db())