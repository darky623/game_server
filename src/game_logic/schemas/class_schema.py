from pydantic import BaseModel
from typing import Optional
from src.game_logic.schemas.params_schema import AddMultiplierParamsSchema, AddSummandParamsSchema
from src.game_logic.schemas.ability_schema import AddAbilitySchema, AbilitySchema


class AddCharacterSubclassSchema(BaseModel):
    title: str
    icon: str
    multiplier_params: AddMultiplierParamsSchema
    summand_params: AddSummandParamsSchema
    abilities: Optional[list[AddAbilitySchema] | list[int]] = []


class AddCharacterClassSchema(BaseModel):
    title: str
    icon: str
    multiplier_params: AddMultiplierParamsSchema
    summand_params: AddSummandParamsSchema
    subclasses: Optional[list[AddCharacterSubclassSchema]] = []
    abilities: Optional[list[int]] = []



class CharacterSubclassSchema(AddCharacterSubclassSchema):
    id: int
    abilities: list[AbilitySchema]

    class Config:
        from_attributes = True


class CharacterClassSchema(AddCharacterClassSchema):
    id: int
    subclasses: Optional[list[CharacterSubclassSchema]] = []
    abilities: Optional[list[AbilitySchema]]

    class Config:
        from_attributes = True

