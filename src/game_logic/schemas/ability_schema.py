from typing import Any

from pydantic import BaseModel, Json, Field
from typing_extensions import Optional, Dict

from src.game_logic.schemas.params_schema import AddMultiplierParamsSchema, AddSummandParamsSchema


class AddAbilityTypeSchema(BaseModel):
    name: str

    class Config:
        from_attributes = True


class AbilityTypeSchema(AddAbilityTypeSchema):
    id: int


class AddAbilitySchema(BaseModel):
    name: str
    icon: str = '#'
    visual: str = 'noetic'
    tier: int

    multiplier_params: Optional[AddMultiplierParamsSchema] = None
    summand_params: Optional[AddSummandParamsSchema] = None

    ability_type_id: int
    summoned_character_id: Optional[int] = None
    summoned_quantity: Optional[int] = None

    chance: Optional[float] = 1
    effect: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target: Optional[str] = 'self'
    trigger_condition: str
    damage: int = 0
    healing: int = 0

    class Config:
        from_attributes = True


class AbilitySchema(AddAbilitySchema):
    id: int
    effect: str | dict
    ability_type: AbilityTypeSchema