from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from src.game_logic.schemas.inventory_schemas import StackBase


class CraftingAttemptRequest(BaseModel):
    ingredients: Dict[str, int]  # {"item_id": quantity}
    applied_boosters: Optional[Dict[str, int]] = None


class CraftingAttemptResponse(BaseModel):
    success: bool
    crafted_item_id: Optional[int] = None
    message: str

    class Config:
        from_attributes = True


class RecipeResponse(BaseModel):
    id: int
    success_chance: Optional[float] = 75.0
    max_crafts: Optional[int]
    is_active: bool
    ingredients: List[StackBase]
    rarity: int
    result_item_id: int
    result_quantity: int

    class Config:
        from_attributes = True


class KnownRecipeResponse(BaseModel):
    id: int
    recipe_id: int
    user_id: int
    success_chance: float
    known_ingredients: Optional[List[StackBase]]
    recipe: Optional[RecipeResponse] = None

    class Config:
        from_attributes = True


class RecipeCreateRequest(BaseModel):
    success_chance: float = 75.0
    max_crafts: Optional[int] = None
    ingredients: List[StackBase]
    rarity: int
    result_item_id: int
    result_quantity: int = 1
    is_active: bool = True

    @field_validator("rarity")
    def validate_rarity(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rarity must be between 1 and 5")
        return v

    @field_validator("ingredients")
    def validate_ingredients(cls, v):
        if not 1 <= len(v) <= 6:
            raise ValueError("Recipe must have between 1 and 6 ingredients")
        return v
