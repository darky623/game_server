from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from bioms.router_biome import router as biome_router
from bioms.router_player_progress import router as player_progress_router
from chat.router import router as chat_router
from chat.websocket import router as chat_websocket_router
from friends.router import router as friends_router
from game_logic.router import router as game_logic_router
from clan.routers.crud_router import router as clan_router
from clan.routers.subscribe_router import router as subscribe_clan_router


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
