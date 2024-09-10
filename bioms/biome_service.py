from sqlalchemy import select

from bioms.schemas import BiomeCreateSchema, BiomeSchema
from bioms.models import Biome


class BiomeService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_biome(self, biome: BiomeCreateSchema) -> BiomeSchema:
        async with self.session_factory() as session:
            biome = Biome(**biome.dict())
            session.add(biome)
            await session.commit()
            await session.refresh(biome)
            return biome

    async def get_biome(self, biome_id: int) -> BiomeSchema:
        async with self.session_factory() as session:
            result = await session.execute(select(Biome).where(Biome.id == biome_id))
            biome = result.scalars().first()
            return biome

    async def get_biomes(self) -> list[BiomeSchema]:
        async with self.session_factory() as session:
            result = await session.execute(select(Biome))
            biomes = result.scalars().all()
            return biomes

    async def update_biome(self, biome_id: int, updated_biome: BiomeCreateSchema) -> BiomeSchema:
        async with self.session_factory() as session:
            result = await session.execute(select(Biome).where(Biome.id == biome_id))
            biome = result.scalars().first()
            if not biome:
                raise ValueError("Biome not found")

            for key, value in updated_biome.dict().items():
                setattr(biome, key, value)

            await session.commit()
            await session.refresh(biome)
            return biome

    async def delete_biome(self, biome_id: int):
        async with self.session_factory() as session:
            result = await session.execute(select(Biome).where(Biome.id == biome_id))
            biome = result.scalars().first()
            if not biome:
                raise ValueError("Biome not found")

            await session.delete(biome)
            await session.commit()
