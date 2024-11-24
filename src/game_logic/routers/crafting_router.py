from fastapi import APIRouter, Depends, HTTPException
from typing import List

from auth import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.schemas.crafting_schemas import (
    CraftingAttemptRequest,
    CraftingAttemptResponse,
    KnownRecipeResponse,
    RecipeResponse,
)
from src.game_logic.services.general import Services

router = APIRouter(prefix="/crafting", tags=["crafting"])


@router.post(
    "/attempt",
    response_model=CraftingAttemptResponse,
    dependencies=[Depends(get_current_user)]
)
async def attempt_craft(
    request: CraftingAttemptRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> CraftingAttemptResponse:
    """
    Attempt to craft items using the provided ingredients.
    The ingredients will be consumed regardless of success.
    """
    result = await services.crafting_service.attempt_craft(
        current_user.id,
        request.ingredients
    )
    return CraftingAttemptResponse(**result)


@router.get(
    "/recipes",
    response_model=List[RecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_active_recipes(
    services: Services = Depends(get_services),
) -> List[RecipeResponse]:
    """Get all active recipes that can be crafted"""
    recipes = await services.crafting_service.get_active_recipes()
    return [RecipeResponse.from_orm(recipe) for recipe in recipes]


@router.get(
    "/known-recipes",
    response_model=List[KnownRecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_known_recipes(
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> List[KnownRecipeResponse]:
    """Get all recipes that the current user has attempted"""
    known_recipes = await services.crafting_service.get_known_recipes(current_user.id)
    return [KnownRecipeResponse.from_orm(recipe) for recipe in known_recipes]
