from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from chat.router import router as chat_router
from chat.websocket import router as chat_websocket_router

app = FastAPI()

app.include_router(chat_router)
app.include_router(chat_websocket_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)