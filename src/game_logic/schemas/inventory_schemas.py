from pydantic import BaseModel

from src.game_logic.schemas.item_schema import ItemSchema


class StackBase(BaseModel):
    item_id: int
    quantity: int


class StackCreate(StackBase):
    inventory_id: int


class StackResponse(StackBase):
    id: int

    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    user_id: int


class InventoryCreate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: int
    stacks: list[StackResponse] = []

    class Config:
        from_attributes = True
