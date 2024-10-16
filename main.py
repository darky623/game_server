from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.bioms.router_biome import router as biome_router
from src.bioms.router_player_progress import router as player_progress_router
from src.chat.router import router as chat_router
from src.chat.websocket import router as chat_websocket_router
from src.friends.router import router as friends_router
from src.game_logic.router import router as game_logic_router
from src.clan.routers.crud_router import router as clan_router
from src.clan.routers.subscribe_router import router as subscribe_clan_router


app = FastAPI()


app.include_router(chat_router)
app.include_router(chat_websocket_router)
app.include_router(biome_router)
app.include_router(player_progress_router)
app.include_router(friends_router)
app.include_router(game_logic_router)
app.include_router(clan_router)
app.include_router(subscribe_clan_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
