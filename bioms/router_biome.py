from fastapi import APIRouter, Depends

from bioms.biome_service import BiomeService
from database import AsyncSessionFactory

from bioms.schemas import BiomeSchema, BiomeCreateSchema

from auth.user_service import get_current_user

router = APIRouter(prefix="/biome", tags={"biome"})
biome_service = BiomeService(AsyncSessionFactory)


@router.post('', response_model=BiomeCreateSchema, dependencies=[Depends(get_current_user)])
async def create_biome(biome: BiomeCreateSchema):
    new_biome = await biome_service.create_biome(biome)
    return new_biome


@router.get('/{biome_id}', response_model=BiomeSchema, dependencies=[Depends(get_current_user)])
async def get_biome(biome_id: int):
    return await biome_service.get_biome(biome_id)


@router.get('', response_model=list[BiomeSchema], dependencies=[Depends(get_current_user)])
async def get_all_biomes():
    return await biome_service.get_biomes()


@router.put('/{biome_id}', response_model=BiomeSchema, dependencies=[Depends(get_current_user)])
async def update_biome(biome_id: int, biome: BiomeCreateSchema):
    return await biome_service.update_biome(biome_id, biome)


@router.delete('/{biome_id}', dependencies=[Depends(get_current_user)])
async def delete_biome(biome_id: int):
    await biome_service.delete_biome(biome_id)
