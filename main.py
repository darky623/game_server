from fastapi import FastAPI, Depends
from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from auth.models import User
from auth.user_service import get_current_user
from bioms.router_biome import router as biome_router
from bioms.router_player_progress import router as player_progress_router
from chat.router import router as chat_router
from chat.websocket import router as chat_websocket_router
from friends.router import router as friends_router
from database import AsyncSessionFactory
from game_logic.models import Character, CharacterClass
from game_logic.router import router as game_logic_router
from clan.router import router as clan_router

from schemas import CreateCharacterSchema

app = FastAPI()


app.include_router(chat_router)
app.include_router(chat_websocket_router)
app.include_router(biome_router)
app.include_router(player_progress_router)
app.include_router(friends_router)
app.include_router(game_logic_router)
app.include_router(clan_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
