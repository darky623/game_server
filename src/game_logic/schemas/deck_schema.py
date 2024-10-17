from typing import List

from pydantic import BaseModel


class DeckCharacter(BaseModel):
    deck_id: int
    character_id: int
    position: int

    class Config:
        json_schema_extra = {"example": {"deck_id": 1, "character_id": 123, "position": 1}}


class Deck(BaseModel):
    user_id: int
    is_active: bool = False
    deck_index: int
    characters: List[DeckCharacter] = []

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "is_active": False,
                "deck_index": 1,
                "characters": [
                    {"deck_id": 1, "character_id": 123, "position": 1},
                    {"deck_id": 1, "character_id": 456, "position": 2},
                ],
            }
        }

