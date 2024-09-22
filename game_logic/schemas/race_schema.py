from pydantic import BaseModel
from typing_extensions import Optional

from game_logic.schemas.ability_schema import AddAbilitySchema
from game_logic.schemas.params_schema import AddSummandParamsSchema, AddMultiplierParamsSchema


class AddRaceSchema(BaseModel):
    name: str
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema
    abilities: Optional[list[int] | list[AddAbilitySchema]] = []


class RaceSchema(AddRaceSchema):
    id: int

    class Config:
        from_attributes = True