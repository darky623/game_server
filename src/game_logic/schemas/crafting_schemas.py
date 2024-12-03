from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from src.game_logic.schemas.inventory_schemas import StackBase


class CraftAttemptResponse(BaseModel):
    """Ответ на попытку крафта"""
    success: bool
    crafted_item_id: Optional[int] = None
    crafted_quantity: Optional[int] = None
    discovered_recipes: List['DiscoveredRecipeInfo'] = []
    message: str
    # Добавляем новые поля для более подробной информации
    used_ingredients: List[Dict[str, Any]] = []  # Использованные ингредиенты
    used_boosters: List[Dict[str, Any]] = []  # Использованные бустеры
    recipe_id: Optional[int] = None  # ID найденного рецепта
    craft_chance: Optional[float] = None  # Шанс успеха крафта
    discovery_mode: bool = False  # Был ли это режим исследования (когда рецепт не найден полностью)

    class Config:
        from_attributes = True


class RecipeResponse(BaseModel):
    id: int
    success_chance: Optional[float] = 75.0
    max_crafts: Optional[int]
    is_active: bool
    is_secret: bool = False
    ingredients: Optional[List[StackBase]] = None  # None если ингредиенты неизвестны
    rarity: int
    result_item_id: int
    result_quantity: int

    class Config:
        from_attributes = True


class KnownRecipeResponse(BaseModel):
    id: int
    recipe_id: int
    user_id: int
    current_success_chance: float
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
    is_secret: bool = False

    @field_validator('rarity')
    def validate_rarity(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rarity must be between 1 and 5')
        return v

    @field_validator('ingredients')
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('Recipe must have at least one ingredient')
        return v

    class Config:
        from_attributes = True


class DiscoveredRecipeInfo(BaseModel):
    """Информация об отгаданном рецепте"""
    recipe_id: int
    result_item_id: int
    discovery_progress: float
    known_ingredients: List[Dict[str, Any]]


class RecipeUpdateRequest(BaseModel):
    """Запрос на обновление рецепта"""
    success_chance: float | None = None
    is_active: bool | None = None


class CraftAttemptRequest(BaseModel):
    ingredients: List[StackBase]
    applied_boosters: Optional[List[StackBase]] = None
    craft_count: int = 1

    @field_validator('craft_count')
    def validate_craft_count(cls, v):
        if v < 1:
            raise ValueError('Craft count must be at least 1')
        if v > 10:  # Ограничиваем максимальное количество крафтов за раз
            raise ValueError('Cannot craft more than 10 items at once')
        return v

    @field_validator('ingredients')
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('Must provide at least one ingredient')
        if len(v) > 6:
            raise ValueError('Cannot use more than 6 ingredients')
        return v

    @field_validator('applied_boosters')
    def validate_boosters(cls, v):
        if v and len(v) > 3:
            raise ValueError('Cannot use more than 3 boosters at once')
        return v


class ShareRecipeRequest(BaseModel):
    """Запрос на передачу рецепта другому игроку"""
    recipe_id: int
    target_user_id: int

    class Config:
        from_attributes = True
