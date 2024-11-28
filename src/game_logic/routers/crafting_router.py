from fastapi import APIRouter, Depends, HTTPException
from typing import List

from auth import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.schemas.crafting_schemas import (
    CraftingAttemptRequest,
    CraftAttemptResponse,
    KnownRecipeResponse,
    RecipeResponse,
    RecipeCreateRequest,
)
from src.game_logic.services.general import Services

router = APIRouter(prefix="/crafting", tags=["crafting"])


@router.get(
    "/recipes",
    response_model=List[RecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_active_recipes(
    services: Services = Depends(get_services),
) -> List[RecipeResponse]:
    """Получить список всех активных рецептов, доступных для крафта"""
    recipes = await services.crafting_service.get_all_recipes()
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get(
    "/known_recipes",
    response_model=List[KnownRecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_known_recipes(
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> List[KnownRecipeResponse]:
    """Получить список всех известных рецептов текущего пользователя"""
    recipes = await services.crafting_service.get_known_recipes(current_user.id)
    return [KnownRecipeResponse.model_validate(recipe) for recipe in recipes]


@router.post(
    "/attempt",
    response_model=CraftAttemptResponse,
    dependencies=[Depends(get_current_user)]
)
async def attempt_craft(
    request: CraftingAttemptRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> CraftAttemptResponse:
    """
    Попытка создать предмет используя указанные ингредиенты.
    Ингредиенты будут потрачены независимо от успеха крафта.
    При желании можно использовать бустеры для увеличения шанса успеха.
    """
    result = await services.crafting_service.attempt_craft(
        current_user.id,
        request.ingredients,
        request.applied_boosters if hasattr(request, 'applied_boosters') else None
    )
    return CraftAttemptResponse.model_validate(result)


@router.post(
    "/recipes/create",
    response_model=RecipeResponse,
    dependencies=[Depends(get_current_user)]
)
async def create_recipe(
    request: RecipeCreateRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> RecipeResponse:
    """Создание нового рецепта"""
    recipe = await services.crafting_service.create_recipe(request)
    return RecipeResponse.model_validate(recipe)
