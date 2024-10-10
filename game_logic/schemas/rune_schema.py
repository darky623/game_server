from pydantic import BaseModel

from game_logic.schemas.params_schema import AddSummandParamsSchema, AddMultiplierParamsSchema


class AddRuneSchema(BaseModel):
    name: str
    level: int
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema
    ability_ids: list[int] = []

    class Config:
        orm_mode = True


class RuneSchema(AddRuneSchema):
    id: int

