from typing import Optional

from pydantic import BaseModel
from pydantic.v1 import root_validator

from src.game_logic.models.models import Character
from src.game_logic.schemas.ability_schema import AbilitySchema
from src.game_logic.schemas.class_schema import CharacterClassSchema, CharacterSubclassSchema
from src.game_logic.schemas.item_schema import ItemSchema
from src.game_logic.schemas.params_schema import AddSummandParamsSchema, AddMultiplierParamsSchema
from src.game_logic.schemas.race_schema import RaceSchema


class AddCharacterSchema(BaseModel):
    name: str
    avatar: Optional[str] = '#'

    race_id: int
    class_id: int
    subclass_id: int
    character_type: str

    summand_params: Optional[AddSummandParamsSchema] = AddSummandParamsSchema()
    multiplier_params: Optional[AddMultiplierParamsSchema] = AddMultiplierParamsSchema()

    item_ids: Optional[list[int]] = []
    ability_ids: Optional[list[int]] = []

    stardom: int
    level: int
    power: Optional[int] = None

    class Config:
        from_attributes = True


class CharacterSchema(AddCharacterSchema):
    id: int
    abilities: list[AbilitySchema]
    items: list[ItemSchema]
    race: RaceSchema
    character_class: CharacterClassSchema
    subclass: CharacterSubclassSchema

    class Config:
        from_attributes = True


class EditCharacterSchema(BaseModel):
    name: str = None
    avatar: Optional[str] = None

    race_id: Optional[int] = None
    class_id: Optional[int] = None
    subclass_id: Optional[int] = None
    character_type: Optional[str] = None

    summand_params: Optional[AddSummandParamsSchema] = None
    multiplier_params: Optional[AddMultiplierParamsSchema] = None

    item_ids: Optional[list[int]] = []
    ability_ids: Optional[list[int]] = []

    stardom: Optional[int] = None
    level: Optional[int] = None

    class Config:
        from_attributes = True
