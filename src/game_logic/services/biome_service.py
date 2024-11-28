from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.game_logic.schemas.biome_schema import BiomeCreateSchema, BiomeSchema
from src.game_logic.models.biome_models import Biome
from src.game_logic.services.service import Service


class BiomeService(Service):

    async def create_biome(self, biome: BiomeCreateSchema) -> BiomeSchema:

        try:
            result = await self.session.execute(select(Biome).where(Biome.name == biome.name))
            if result.scalars().first():
                raise HTTPException(409, "Biome with that name already exists")
            new_biome = Biome(**biome.dict())
            await super().add(new_biome)
            await self.session.refresh(new_biome)  # Refresh to get the id
            return BiomeSchema.from_orm(new_biome)
        except SQLAlchemyError as e:
            raise HTTPException(500, "Error creating biome") from e

    async def get_biome(self, biome_id: int) -> BiomeSchema:

        try:
            result = await self.session.execute(
                select(Biome).where(Biome.id == biome_id)
            )
            biome = result.scalars().first()
            if biome is None:
                raise HTTPException(404, "Biome with this ID not found")
            return BiomeSchema.from_orm(biome)

        except SQLAlchemyError as e:
            raise HTTPException(500, "Error getting biome") from e

    async def get_biomes(self) -> list[BiomeSchema]:
        try:
            result = await self.session.execute(select(Biome))
            biomes = result.scalars().all()
            if biomes is None:
                raise HTTPException(404, "Biomes not found")
            return [BiomeSchema.from_orm(biome) for biome in biomes]
        except SQLAlchemyError as e:
            raise HTTPException(500, "Error getting biomes") from e

    async def update_biome(self, biome_id: int,
                           updated: BiomeCreateSchema
                           ) -> BiomeSchema:

        try:
            result = await self.session.execute(
                select(Biome).where(Biome.id == biome_id)
            )
            biome = result.scalars().first()
            if biome is None:
                raise HTTPException(404, "Biome with this ID not found")

            for key, value in updated.dict().items():
                if hasattr(biome, key):  # Проверяем, что у биома есть такое поле
                    setattr(biome, key, value)

            await super().add(updated)

        except SQLAlchemyError as e:
            raise HTTPException(500, "Error updating biome") from e

    async def delete_biome(self, biome_id: int):
        try:
            result = await self.session.execute(
                select(Biome).where(Biome.id == biome_id)
            )
            biome = result.scalars().first()
            if biome is None:
                raise HTTPException(404, "Biome with this ID not found")

            await self.session.delete(biome)
            await self.session.commit()

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(500, "Error deleting biome") from e

    async def get_biome_by_name(self, name: str) -> BiomeSchema:
        try:
            result = await self.session.execute(select(Biome).where(Biome.name == name))
            biome = result.scalars().first()
            if biome is None:
                raise HTTPException(404, "Biome with this name not found")
            return BiomeSchema.from_orm(biome)
        except SQLAlchemyError as e:
            raise HTTPException(500, "Error getting biome") from e
