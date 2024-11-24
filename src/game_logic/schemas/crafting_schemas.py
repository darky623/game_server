from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from src.game_logic.schemas.inventory_schemas import StackBase


class CraftingAttemptResponse(BaseModel):
    """Response model for crafting attempts"""
    success: bool
    message: str
    crafted_item_id: Optional[int] = None
    quantity: Optional[int] = None


class KnownRecipeResponse(BaseModel):
    """Response model for known recipes"""
    recipe_id: int
    known_ingredients: Dict[str, int]
    success_rate: float

    class Config:
        orm_mode = True


class RecipeResponse(BaseModel):
    """Response model for recipes"""
    id: int
    ingredients: Dict[str, int]
    result_item_id: int
    result_quantity: int
    is_active: bool
    base_success_rate: float

    class Config:
        orm_mode = True


class CraftingAttemptRequest(BaseModel):
    """Request model for crafting attempts"""
    ingredients: List[StackBase] = Field(..., min_items=1, max_items=6)
