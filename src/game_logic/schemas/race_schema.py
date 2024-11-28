from pydantic import BaseModel
from typing_extensions import Optional

from src.game_logic.schemas.ability_schema import AddAbilitySchema, AbilitySchema
from src.game_logic.schemas.params_schema import AddSummandParamsSchema, AddMultiplierParamsSchema


class AddRaceSchema(BaseModel):
    name: str
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema
    abilities: Optional[list[int] | list[AddAbilitySchema]] = []


class RaceSchema(AddRaceSchema):
    id: int
    abilities: list[AbilitySchema]

    class Config:
        from_attributes = True