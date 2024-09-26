from fastapi import APIRouter, Depends, HTTPException

from auth.models import User
from auth.user_service import get_current_user

from clan.clan_service import ClanService
from clan.schemas import ClanSchemaCreate, ClanSchema
from database import AsyncSessionFactory
from typing import Optional

router = APIRouter(prefix='/clan')
clan_service = ClanService(AsyncSessionFactory)


@router.post('/create', response_model=ClanSchemaCreate)
async def create_clan(clan: ClanSchemaCreate, user: User = Depends(get_current_user)):
    return await clan_service.create_clan(clan, user.id)


# @router.get('/{clan_id}', response_model=ClanSchema)
# async def get_clan(clan_id: int, user: User = Depends(get_current_user)):

