
from fastapi import APIRouter, Depends, HTTPException

from auth.models import User
from auth.user_service import get_current_user

from bioms.player_progress_service import PlayerProgressService
from bioms.schemas import PlayerProgressSchema
from database import AsyncSessionFactory

router = APIRouter(prefix="/player_progress")
service = PlayerProgressService(AsyncSessionFactory)


@router.get('/{user_id}', response_model=PlayerProgressSchema)
async def get_player_progress(user_id: int) -> PlayerProgressSchema:
    return await service.get_player_progress(user_id)


@router.post('', response_model=PlayerProgressSchema)
async def create_player_progress(user: User = Depends(get_current_user)) -> PlayerProgressSchema:
    return await service.create_player_progress(user.id)


@router.patch('/{user_id}', response_model=PlayerProgressSchema)
async def update_player_progress(update: PlayerProgressSchema) -> PlayerProgressSchema:
    return await service.update_player_progress(update)


@router.delete('/{user_id}')
async def delete_player_progress(user_id: int):
    await service.delete_player_progress(user_id)
