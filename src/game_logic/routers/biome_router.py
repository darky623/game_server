from typing import List

from fastapi import APIRouter, Depends

from config.deps import get_services
from src.game_logic.schemas.biome_schema import BiomeSchema, BiomeCreateSchema

from auth.user_service import get_current_user
from src.game_logic.services.general import Services

router = APIRouter(prefix="/biome", tags=["biome"])


@router.post('', response_model=BiomeCreateSchema, dependencies=[Depends(get_current_user)])
async def create_biome(biome: BiomeCreateSchema,
                       services: Services = Depends(get_services)
                       ) -> BiomeCreateSchema:
    new_biome = await services.biome_service.create_biome(biome)
    return new_biome


@router.get('/{biome_id}', response_model=BiomeSchema, dependencies=[Depends(get_current_user)])
async def get_biome(biome_id: int,
                    services: Services = Depends(get_services)
                    ) -> BiomeSchema:
    return await services.biome_service.get_biome(biome_id)


@router.get('', response_model=List[BiomeSchema], dependencies=[Depends(get_current_user)])
async def get_all_biomes(services: Services = Depends(get_services)) -> List[BiomeSchema]:
    return await services.biome_service.get_biomes()


@router.put('/{biome_id}', response_model=BiomeSchema, dependencies=[Depends(get_current_user)])
async def update_biome(biome_id: int,
                       biome: BiomeCreateSchema,
                       services: Services = Depends(get_services)
                       ) -> BiomeSchema:
    return await services.biome_service.update_biome(biome_id, biome)


@router.delete('/{biome_id}', dependencies=[Depends(get_current_user)])
async def delete_biome(biome_id: int,
                       services: Services = Depends(get_services)
                       ) -> None:
    await services.biome_service.delete_biome(biome_id)
