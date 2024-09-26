from fastapi import FastAPI, Depends
from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from auth.models import User
from auth.user_service import get_current_user
from chat.router import router as chat_router
from chat.websocket import router as chat_websocket_router
from database import AsyncSessionFactory
from game_logic.models import Character, CharacterClass
from game_logic.router import router as game_logic_router

from schemas import CreateCharacterSchema

app = FastAPI()


app.include_router(chat_router)

app.include_router(chat_websocket_router)
app.include_router(game_logic_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)