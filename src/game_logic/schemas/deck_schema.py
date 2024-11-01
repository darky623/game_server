from typing import List

from pydantic import BaseModel

from src.game_logic.schemas.ability_schema import AbilitySchema
from src.game_logic.schemas.character_schema import CharacterSchema
from src.game_logic.schemas.class_schema import CharacterClassSchema, CharacterSubclassSchema
from src.game_logic.schemas.item_schema import ItemSchema
from src.game_logic.schemas.race_schema import RaceSchema


class DeckCharacter(BaseModel):
    id: int
    deck_id: int
    character_id: int
    position: int
    character: CharacterSchema

    class Config:
        from_attributes = True


class Deck(BaseModel):
    id: int
    user_id: int
    is_active: bool = False
    deck_index: int
    characters: List[DeckCharacter]

    class Config:
        from_attributes = True
