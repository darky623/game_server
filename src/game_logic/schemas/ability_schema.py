from pydantic import BaseModel
from typing_extensions import Optional

from src.game_logic.schemas.params_schema import AddMultiplierParamsSchema, AddSummandParamsSchema


class AddAbilityTypeSchema(BaseModel):
    name: str

    class Config:
        from_attributes = True


class AbilityTypeSchema(AddAbilityTypeSchema):
    id: int


class AddAbilitySchema(BaseModel):
    name: str
    icon: str
    tier: int

    multiplier_params: Optional[AddMultiplierParamsSchema] = None
    summand_params: Optional[AddSummandParamsSchema] = None

    ability_type_id: int
    summoned_character_id: Optional[int] = None
    summoned_quantity: int = 0

    trigger_condition: str
    damage: int = 0
    healing: int = 0

    class Config:
        from_attributes = True


class AbilitySchema(AddAbilitySchema):
    id: int
    ability_type: AbilityTypeSchema