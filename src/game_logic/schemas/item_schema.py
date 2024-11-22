from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from src.game_logic.schemas.params_schema import (
    AddSummandParamsSchema,
    AddMultiplierParamsSchema,
)


class AddItemSchema(BaseModel):
    name: str
    item_type: Optional[str]
    is_stacked: bool = False
    item_data: Optional[Dict[str, Any]]
    level: Optional[int] = None
    icon: Optional[str] = None
    is_personal: bool = False
    tier: int = Field(ge=0, le=5)
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema


class ItemSchema(AddItemSchema):
    id: int

    class Config:
        from_attributes = True


class GetItemsSchema(BaseModel):
    item_ids: list = []
