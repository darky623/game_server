from fastapi import APIRouter, Depends, HTTPException
from chat.schemas import AddChatSchema, ChatSchema
from auth.models import User
from auth.user_service import get_current_user

from clan.clan_service import ClanService
from database import AsyncSessionFactory
from typing import Optional

router = APIRouter(prefix='/chat')
clan_service = ClanService(AsyncSessionFactory)
