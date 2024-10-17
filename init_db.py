import asyncio
from config.database import engine, Base, AsyncSessionFactory


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(Base.metadata.create_all)
        # await create_archetypes()
        # await create_character_types()


if __name__ == '__main__':
    asyncio.run(init_db())


# from config import config
# from game_logic.models.models import CharacterArchetype
# async def create_archetypes():
#     archetypes = []
#     async with AsyncSessionFactory() as db:
#         for archetype in config.archetypes:
#             archetypes.append(CharacterArchetype(title=archetype['title']))
#         db.add_all(archetypes)
#         await db.commit()
#
#
# async def create_character_types():
#     character_types = []
#     async with AsyncSessionFactory() as db:
#         for character_type in config.character_types:
#             character_types.append(CharacterArchetype(name=character_type['name']))
#         db.add_all(character_types)
#         await db.commit()
#

