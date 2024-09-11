from fastapi import APIRouter

from bioms.biome_service import BiomeService
from database import AsyncSessionFactory

from bioms.schemas import BiomeSchema, BiomeCreateSchema

router = APIRouter(prefix="/biome")
biome_service = BiomeService(AsyncSessionFactory)


@router.post('', response_model=BiomeCreateSchema)
async def create_biome(biome: BiomeCreateSchema):
    new_biome = await biome_service.create_biome(biome)
    return new_biome


@router.get('/{biome_id}', response_model=BiomeSchema)
async def get_biome(biome_id: int):
    return await biome_service.get_biome(biome_id)


@router.get('', response_model=list[BiomeSchema])
async def get_all_biomes():
    return await biome_service.get_biomes()


@router.put('/{biome_id}', response_model=BiomeSchema)
async def update_biome(biome_id: int, biome: BiomeCreateSchema):
    return await biome_service.update_biome(biome_id, biome)


@router.delete('/{biome_id}')
async def delete_biome(biome_id: int):
    await biome_service.delete_biome(biome_id)
