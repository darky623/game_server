from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.chat.schemas import ChatSchema
from src.game_logic.schemas.character_schema import CharacterSchema


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    characters: Optional[list[CharacterSchema]] = []
    create_date: Optional[datetime]
    chats: list[ChatSchema]

    class Config:
        from_attributes = True
