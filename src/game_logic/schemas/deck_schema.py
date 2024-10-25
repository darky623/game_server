from typing import List

from pydantic import BaseModel

from src.game_logic.schemas.ability_schema import AbilitySchema
from src.game_logic.schemas.character_schema import CharacterSchema
from src.game_logic.schemas.class_schema import CharacterClassSchema, CharacterSubclassSchema
from src.game_logic.schemas.item_schema import ItemSchema
from src.game_logic.schemas.race_schema import RaceSchema


class DeckCharacter(BaseModel):
    deck_id: int
    character: CharacterSchema
    position: int

    class Config:
        json_schema_extra = {
            "example":
                {"deck_id": 1,
                 "position": 1,
                 "character": [
                         {"id": 1,
                          "abilities": list[AbilitySchema],
                          "items": list[ItemSchema],
                          "race": RaceSchema,
                          "character_class": CharacterClassSchema,
                          "subclass": CharacterSubclassSchema
                          },],
                 }
        }


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
