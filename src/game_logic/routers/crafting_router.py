from fastapi import APIRouter, Depends, HTTPException
from typing import List

from auth import User
from auth.user_service import get_current_user
from config.deps import get_services
from src.game_logic.energy.energy_decorators import require_energy

from src.game_logic.schemas.crafting_schemas import (
    CraftAttemptResponse,
    KnownRecipeResponse,
    RecipeResponse,
    RecipeCreateRequest,
    StackBase, RecipeUpdateRequest, CraftAttemptRequest, ShareRecipeRequest
)
from src.game_logic.services.general import Services

router = APIRouter(prefix="/crafting", tags=["crafting"])


@router.get(
    "/recipes",
    response_model=List[RecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_active_recipes(
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> List[RecipeResponse]:
    """Получить список всех активных несекретных рецептов"""
    recipes = await services.crafting_service.get_all_recipes()
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get(
    "/recipes/{recipe_id}",
    response_model=RecipeResponse,
    dependencies=[Depends(get_current_user)]
)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> RecipeResponse:
    """Получить рецепт по ID"""
    recipe = await services.crafting_service.get_recipe(recipe_id, current_user.id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get(
    "/known_recipes",
    response_model=List[KnownRecipeResponse],
    dependencies=[Depends(get_current_user)]
)
async def get_known_recipes(
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> List[KnownRecipeResponse]:
    """Получить список всех известных рецептов пользователя с известными ингредиентами"""
    known_recipes = await services.crafting_service.get_known_recipes(current_user.id)
    
    response = []
    for kr in known_recipes:
        # Конвертируем Recipe в RecipeResponse
        recipe = RecipeResponse.model_validate(kr.recipe)
        
        # Конвертируем known_ingredients в правильный формат, если он существует
        known_ingredients = []
        if kr.known_ingredients:
            for ingredient in kr.known_ingredients:
                if isinstance(ingredient, dict) and 'item_id' in ingredient and 'quantity' in ingredient:
                    known_ingredients.append(StackBase(
                        item_id=ingredient['item_id'],
                        quantity=ingredient['quantity']
                    ))
        
        response.append(KnownRecipeResponse(
            id=kr.id,
            recipe_id=kr.recipe_id,
            user_id=kr.user_id,
            current_success_chance=kr.current_success_chance,
            known_ingredients=known_ingredients,
            recipe=recipe
        ))
    
    return response


@router.post(
    "/attempt",
    response_model=CraftAttemptResponse,
    dependencies=[Depends(get_current_user)]
)
@require_energy(energy_amount=10)  # Требуется 10 единиц энергии для попытки крафта
async def attempt_craft(
    request: CraftAttemptRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> CraftAttemptResponse:
    """
    Попытка создать предмет используя указанные ингредиенты.
    Требует 10 единиц энергии за попытку крафта.
    Ингредиенты будут потрачены независимо от успеха крафта.
    При желании можно использовать бустеры для увеличения шанса успеха.
    """
    return await services.crafting_service.attempt_craft(
        user_id=current_user.id,
        ingredients=request.ingredients,
        applied_boosters=request.applied_boosters,
        craft_count=request.craft_count
    )


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


@router.put(
    "/recipes/{recipe_id}",
    response_model=RecipeResponse,
    dependencies=[Depends(get_current_user)]
)
async def update_recipe(
    recipe_id: int,
    request: RecipeUpdateRequest,
    services: Services = Depends(get_services),
) -> RecipeResponse:
    """Обновить параметры рецепта"""
    recipe = await services.crafting_service.update_recipe(
        recipe_id=recipe_id,
        success_chance=request.success_chance,
        is_active=request.is_active
    )
    return RecipeResponse.model_validate(recipe)


@router.post(
    "/share",
    response_model=bool,
    dependencies=[Depends(get_current_user)]
)
async def share_recipe(
    request: ShareRecipeRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
) -> bool:
    """
    Поделиться рецептом с другим игроком.
    Рецепт должен быть известен текущему пользователю и не должен быть секретным.
    Оба пользователя должны быть в одном клане.
    """
    return await services.crafting_service.share_recipe(
        current_user.id,
        request.recipe_id,
        request.target_user_id
    )
