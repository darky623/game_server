from fastapi import APIRouter, Depends

from auth.models import User
from auth.user_service import get_current_user
from bioms.biome_service import BiomeService
from bioms.player_progress_service import PlayerProgressService
from bioms.schemas import PlayerProgressSchema
from database import AsyncSessionFactory

router = APIRouter(prefix="/player_progress")
service = PlayerProgressService(AsyncSessionFactory)


@router.get('/{user_id}', response_model=PlayerProgressSchema)
async def get_player_progress(user_id: User = Depends(get_current_user)):
    return await service.get_player_progress(user_id)


@router.post('', response_model=PlayerProgressSchema)
async def create_player_progress(player_progress: PlayerProgressSchema):
    return await service.create_player_progress(player_progress)


@router.patch('/{user_id}', response_model=PlayerProgressSchema)
async def update_player_progress(user_id: User = Depends(get_current_user),
                                 player_progress: PlayerProgressSchema = Depends(get_current_user)):
    return await service.update_player_progress(player_progress)


@router.delete('/{user_id}')
async def delete_player_progress(user_id: User = Depends(get_current_user)):
    await service.delete_player_progress(user_id)
