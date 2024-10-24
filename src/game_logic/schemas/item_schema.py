from pydantic import BaseModel

from src.game_logic.schemas.params_schema import AddSummandParamsSchema, AddMultiplierParamsSchema


class AddItemSchema(BaseModel):
    name: str
    level: int
    icon: str
    tier: int
    summand_params: AddSummandParamsSchema
    multiplier_params: AddMultiplierParamsSchema


class ItemSchema(AddItemSchema):
    id: int

    class Config:
        from_attributes = True

class GetItemsSchema(BaseModel):
    item_ids: list = []