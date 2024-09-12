
from fastapi import APIRouter, Depends, HTTPException

from auth.models import User
from auth.user_service import get_current_user

from bioms.player_progress_service import PlayerProgressService
from bioms.schemas import PlayerProgressSchema
from database import AsyncSessionFactory

router = APIRouter(prefix="/player_progress")
service = PlayerProgressService(AsyncSessionFactory)


@router.get('/{user_id}', response_model=PlayerProgressSchema)
async def get_player_progress(user: User = Depends(get_current_user)):
    return await service.get_player_progress(user)


@router.post('/{user_id}', response_model=PlayerProgressSchema)
async def create_player_progress(user: int = Depends(get_current_user)):
    return await service.create_player_progress(user.id)


@router.patch('/{user_id}', response_model=PlayerProgressSchema)
async def update_player_progress(update: PlayerProgressSchema):
    return await service.update_player_progress(update)


@router.delete('/{user_id}')
async def delete_player_progress(user: User = Depends(get_current_user)):
    await service.delete_player_progress(user.id)
