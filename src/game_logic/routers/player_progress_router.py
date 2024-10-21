from fastapi import APIRouter, Depends

from auth.models import User
from auth.user_service import get_current_user
from config.deps import get_services

from src.game_logic.schemas.player_progress_schema import PlayerProgressSchema, PlayerProgressUpdateSchema
from src.game_logic.services.general import Services

router = APIRouter(prefix="/player_progress", tags=['player_progress'])


@router.get("/{user_id}", response_model=PlayerProgressSchema, dependencies=[Depends(get_current_user)])
async def get_player_progress(user_id: int,
                              services: Services = Depends(get_services)
                              ) -> PlayerProgressSchema:
    return await services.player_progress_service.get_player_progress(user_id)


@router.post("", response_model=PlayerProgressSchema, dependencies=[Depends(get_current_user)])
async def create_player_progress(user: User = Depends(get_current_user),
                                 services: Services = Depends(get_services)
                                 ) -> PlayerProgressSchema:
    return await services.player_progress_service.create_player_progress(user.id)


@router.put("/{user_id}", response_model=PlayerProgressUpdateSchema, dependencies=[Depends(get_current_user)])
async def update_player_progress(update: PlayerProgressUpdateSchema,
                                 services: Services = Depends(get_services),
                                 user: User = Depends(get_current_user)
                                 ) -> PlayerProgressSchema:
    return await services.player_progress_service.update_player_progress(update, user.id)


@router.delete("/{user_id}", dependencies=[Depends(get_current_user)])
async def delete_player_progress(user_id: int,
                                 services: Services = Depends(get_services)
                                 ) -> None:
    await services.player_progress_service.delete_player_progress(user_id)

