from pydantic import BaseModel
from typing import Optional
from game_logic.schemas.params_schema import AddMultiplierParamsSchema, AddSummandParamsSchema
from game_logic.schemas.ability_schema import AddAbilitySchema


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
    abilities: Optional[list[AddAbilitySchema] | list[int]] = []



class CharacterSubclassSchema(AddCharacterClassSchema):
    id: int

    class Config:
        from_attributes = True


class CharacterClassSchema(AddCharacterClassSchema):
    id: int
    subclasses: Optional[list[CharacterSubclassSchema]] = []

    class Config:
        from_attributes = True

