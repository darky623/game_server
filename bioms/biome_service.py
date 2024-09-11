from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from bioms.schemas import BiomeCreateSchema, BiomeSchema
from bioms.models import Biome


class BiomeService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_biome(self, biome: BiomeCreateSchema) -> BiomeSchema:
        async with self.session_factory() as session:
            # try:
            print(biome.dict())
            new_biome = Biome(**biome.dict())
            print(new_biome.serialize())
            session.add(new_biome)
            await session.commit()
            await session.refresh(new_biome)
            return new_biome
            # except SQLAlchemyError as e:
            #     await session.rollback()
            #     raise HTTPException(500, "Error creating biome") from e

    async def get_biome(self, biome_id: int) -> BiomeSchema:
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(Biome).where(Biome.id == biome_id)
                )
                biome = result.scalars().first()
                if not biome:
                    raise HTTPException(404, "Biome not found")
                return biome

            except SQLAlchemyError as e:
                raise HTTPException(500, "Error getting biome") from e

    async def get_biomes(self) -> list[BiomeSchema]:
        async with self.session_factory() as session:
            try:
                result = await session.execute(select(Biome))
                biomes = result.scalars().all()
                return biomes
            except SQLAlchemyError as e:
                raise HTTPException(500, "Error getting biomes") from e

    async def update_biome(
        self, biome_id: int, updated: BiomeCreateSchema
    ) -> BiomeSchema:
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(Biome).where(Biome.id == biome_id)
                )
                biome = result.scalars().first()
                if not biome:
                    raise HTTPException(404, "Biome not found")

                for key, value in updated.dict().items():
                    if hasattr(biome, key):  # Проверяем, что у биома есть такое поле
                        setattr(biome, key, value)

                await session.commit()
                await session.refresh(biome)
                return biome
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(500, "Error updating biome") from e

    async def delete_biome(self, biome_id: int):
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(Biome).where(Biome.id == biome_id)
                )
                biome = result.scalars().first()
                if not biome:
                    raise HTTPException(404, "Biome not found")

                await session.delete(biome)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(500, "Error deleting biome") from e
