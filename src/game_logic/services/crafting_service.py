import json
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict

from src.game_logic.models.crafting_models import Recipe, KnownRecipe, CraftAttempt
from src.game_logic.models.inventory_models import Item, Stack
from src.game_logic.schemas.crafting_schemas import (
    RecipeCreateRequest,
    KnownRecipeResponse,
    RecipeResponse,
)
from src.game_logic.schemas.inventory_schemas import StackBase, StackResponse
from src.game_logic.services.service import Service
from src.game_logic.services.inventory_service import InventoryService


class CraftingService(Service):
    inventory_service: InventoryService

    def __init__(self, session):
        super().__init__(session)
        self.inventory_service = InventoryService(session)

    async def attempt_craft(
        self,
        user_id: int,
        ingredients: List[StackBase],
        applied_boosters: List[StackBase] | None = None,
    ):
        """
        Попытка крафта предметов. Игрок может отправить от 1 до 6 ингредиентов.
        Если найден подходящий рецепт и крафт успешен - игрок получает предмет.
        Ингредиенты тратятся в любом случае.
        """
        try:
            # Проверяем количество ингредиентов
            if not (1 <= len(ingredients) <= 6):
                raise HTTPException(
                    status_code=400,
                    detail="Number of ingredients must be between 1 and 6",
                )

            # Проверяем наличие ингредиентов у пользователя
            if not await self.inventory_service.has_items(user_id, ingredients):
                raise HTTPException(
                    status_code=400, detail="Not enough ingredients in inventory"
                )

            # Ищем подходящий активный рецепт
            recipe = await self._find_matching_recipe(ingredients)
            if applied_boosters:
                boosters_stacks = [
                    StackBase(item_id=int(booster.item_id), quantity=booster.quantity)
                    for booster in applied_boosters
                ]
                has_applied_boosters = await self.inventory_service.has_items(
                    user_id, boosters_stacks
                )
                if has_applied_boosters:
                    await self.inventory_service.remove_items(user_id, boosters_stacks)
                    success_chance = await self._calculate_success_chance(
                        recipe, boosters_stacks
                    )
                    recipe.success_chance = success_chance
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No matching recipe or boosters not found",
                    )

            # Удаляем ингредиенты из инвентаря (они тратятся в любом случае)
            await self.inventory_service.remove_items(user_id, ingredients)
            # Преобразуем ингридиенты в словарь для хранения в Json поле попытки крафта
            used_ingredients = {
                "ingredients": [
                    {"item_id": ing.item_id, "quantity": ing.quantity}
                    for ing in ingredients
                ]
            }
            # Создаем запись о попытке крафта
            craft_attempt = CraftAttempt(
                user_id=user_id,
                recipe_id=recipe.id if recipe else None,
                used_ingredients=used_ingredients,
                success_chance=recipe.success_chance if recipe else None,
                applied_boosters=applied_boosters,
            )

            if recipe:
                # Проверяем, открыт ли частично рецепт
                known_recipe = await self._get_or_create_known_recipe(
                    user_id, recipe.id
                )
                # Обновляем известные ингредиенты
                await self._update_known_ingredients(user_id, recipe, ingredients)
                # Если рецепт найден и активен, проверяем шанс успеха
                if recipe.is_active and await self._roll_craft_success(known_recipe):
                    # Крафт успешен
                    craft_attempt.is_successful = True
                    await self.inventory_service.add_items_to_inventory(
                        user_id,
                        [
                            StackBase(
                                item_id=recipe.result_item_id,
                                quantity=recipe.result_quantity,
                            )
                        ],
                    )

                    return {
                        "success": True,
                        "message": "Crafting successful!",
                        "crafted_item_id": recipe.result_item_id,
                        "quantity": recipe.result_quantity,
                    }

            # Сохраняем попытку крафта
            self.session.add(craft_attempt)
            await self.session.commit()

            if not recipe:
                return {"success": False, "message": "No matching recipe found"}

            return {"success": False, "message": "Crafting failed"}

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Database error during crafting from {e}"
            )

    async def _find_matching_recipe(
        self, ingredients: List[StackBase]
    ) -> Optional[Recipe]:
        """Поиск подходящего рецепта по ингредиентам"""
        try:
            # Получаем все рецепты
            result = await self.session.execute(select(Recipe))
            recipes = result.scalars().all()

            for recipe in recipes:
                # Проверяем совпадение ингредиентов и их количества
                recipe_ingredients = recipe.ingredients
                if self._ingredients_full_match(recipe_ingredients, ingredients):
                    return recipe

            return None

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, detail="Error while searching for recipe"
            )

    def _ingredients_full_match(
        self, recipe_ingredients: List[StackBase], provided_ingredients: List[StackBase]
    ) -> bool:
        """Проверка соответствия ингредиентов рецепту"""

        recipe_dict = {ing["item_id"]: ing["quantity"] for ing in recipe_ingredients}

        for ing in provided_ingredients:
            if (
                ing.item_id not in recipe_dict
                or recipe_dict[ing.item_id] > ing.quantity
            ):
                return False

        return True

    # Следует добавить обработку частичного узнавания рецептов(всех рецептов в базе)
    def _ingredients_match(self, ingredients: List[StackBase]) -> List[RecipeResponse]:
        """
        Проверяет совпадения ингредиентов с рецептами в базе данных.
        Возвращает список рецептов, которые частично доступны игроку.
        """

        # Создаем словарь, где ключ - id ингредиента, значение - количество
        ingredient_counts = defaultdict(int)
        for ing in ingredients:
            ingredient_counts[ing.item_id] += ing.quantity

        available_recipes = []
        recipes = (
            self.session.execute(select(Recipe)).scalars().all()
        )  # Загружаем все рецепты

        for recipe in recipes:
            matching_ingredients = 0
            missing_ingredients = []

            # Проверяем наличие ингредиентов рецепта в списке игрока
            for ingredient in recipe.ingredients:
                if ingredient.item_id in ingredient_counts:
                    if ingredient_counts[ingredient.item_id] >= ingredient.quantity:
                        matching_ingredients += 1
                    else:
                        missing_ingredients.append(
                            {
                                "item_id": ingredient.item_id,
                                "quantity": ingredient.quantity
                                - ingredient_counts[ingredient.item_id],
                            }
                        )
                else:
                    missing_ingredients.append(
                        {"item_id": ingredient.item_id, "quantity": ingredient.quantity}
                    )

            # Если найдено хотя бы один ингредиент, добавляем рецепт в список доступных
            if matching_ingredients > 0:
                available_recipes.append(
                    RecipeResponse(
                        recipe_id=recipe.recipe_id,
                        result_item_id=recipe.result_item_id,
                        result_quantity=recipe.result_quantity,
                        ingredients=recipe.ingredients,  # Здесь передаём все ингредиенты рецепта
                        matching_ingredients=matching_ingredients,  # Количество совпавших ингридиентов
                        missing_ingredients=missing_ingredients,  # Список недостающих ингридиентов
                    )
                )

        return available_recipes

    async def _get_or_create_known_recipe(
        self, user_id: int, recipe_id: int
    ) -> KnownRecipe:
        """Получение или создание записи об известном рецепте"""
        result = await self.session.execute(
            select(KnownRecipe).where(
                KnownRecipe.user_id == user_id, KnownRecipe.recipe_id == recipe_id
            )
        )
        known_recipe = result.scalar_one_or_none()
        # Преобразуем ингридиенты в словарь для хранения в Json поле попытки крафта
        # used_ingredients = {
        #     "ingredients": [
        #         {"item_id": ing.item_id, "quantity": ing.quantity} for ing in ingredients
        #     ]
        # }
        if not known_recipe:
            known_recipe = KnownRecipe(
                user_id=user_id,
                recipe_id=recipe_id,
                known_ingredients=None,
                current_success_chance=75.0,
                applied_boosters=[],
            )
            self.session.add(known_recipe)
            await self.session.commit()

        return known_recipe

    async def _update_known_ingredients(
        self,
        user_id: int,
        recipe: RecipeResponse,
        provided_ingredients: List[StackBase],
    ):
        """Обновляет known_ingredients в KnownRecipe, сохраняя предыдущий прогресс."""

        known_recipe = await self.session.execute(
            select(KnownRecipe)
            .where(KnownRecipe.user_id == user_id)
            .where(KnownRecipe.recipe_id == recipe.id)
            .options(joinedload(KnownRecipe.recipe))
        )
        known_recipe = known_recipe.scalar_one_or_none()

        if known_recipe is None:
            known_recipe = KnownRecipe(
                user_id=user_id, recipe_id=recipe.id, known_ingredients=[]
            )  # Инициализируем пустым списком
            self.session.add(known_recipe)

        matched_ingredients = []
        correct_ingredients = 0
        for provided in provided_ingredients:
            for recipe_ing in recipe.ingredients:
                if (
                    provided.item_id == recipe_ing["item_id"]
                    and provided.quantity >= recipe_ing["quantity"]
                ):
                    matched_ingredients.append(
                        {
                            "item_id": provided.item_id,
                            "quantity": provided.quantity,
                        }
                    )
                    correct_ingredients += 1
                    break

        total_ingredients = len(recipe.ingredients)
        should_reveal = False

        if total_ingredients >= 4:
            if total_ingredients == 6:
                should_reveal = correct_ingredients in range(4, 6)
            elif total_ingredients == 5:
                should_reveal = correct_ingredients in range(3, 5)
            elif total_ingredients == 4:
                should_reveal = correct_ingredients in range(2, 4)

        if should_reveal:
            # Преобразуем JSON в список Python, добавляем новые элементы, и обратно в JSON
            current_known = json.loads(
                known_recipe.known_ingredients or "[]"
            )  # Обрабатываем None

            new_ingredients = [
                ing for ing in matched_ingredients if ing not in current_known
            ]
            current_known.extend(new_ingredients)
            known_recipe.known_ingredients = json.dumps(current_known)
            await self.session.commit()

    async def _roll_craft_success(self, known_recipe: KnownRecipe) -> bool:
        """Проверка успешности крафта с учетом шанса"""
        import random

        total_chance = known_recipe.current_success_chance
        for booster in known_recipe.applied_boosters:
            total_chance += booster.get("bonus", 0)

        return random.random() * 100 <= min(total_chance, 100)

    async def _calculate_success_chance(
        self, recipe: RecipeResponse, applied_boosters: List[StackBase]
    ) -> float:
        """Вычисление шанса крафта с учетом примененных усилителей"""
        total_chance = recipe.success_chance
        for booster in applied_boosters:
            total_chance += booster.get("bonus", 0)

        return total_chance

    async def get_known_recipes(self, user_id: int) -> List[KnownRecipeResponse]:
        """Получение всех известных рецептов пользователя"""
        result = await self.session.execute(
            select(KnownRecipe)
            .options(joinedload(KnownRecipe.recipe))
            .where(KnownRecipe.user_id == user_id)
        )

        known_recipes = result.scalars().all()
        return [KnownRecipeResponse.model_validate(r) for r in known_recipes]

    async def toggle_recipe_favorite(self, user_id: int, recipe_id: int) -> KnownRecipe:
        """Добавление/удаление рецепта из избранного"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)
        known_recipe.is_favorite = not known_recipe.is_favorite
        await self.session.commit()
        return known_recipe

    async def apply_booster(
        self, user_id: int, recipe_id: int, booster_id: int, bonus: float
    ) -> KnownRecipe:
        """Применение усилителя к рецепту"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)

        # Проверяем, не применен ли уже такой бустер
        for booster in known_recipe.applied_boosters:
            if booster["booster_id"] == booster_id:
                raise HTTPException(400, "This booster is already applied")

        known_recipe.applied_boosters.append({"booster_id": booster_id, "bonus": bonus})

        await self.session.commit()
        return known_recipe

    async def get_all_active_recipes(self) -> List[RecipeResponse]:
        """
        Получение всех активных рецептов игры
        """
        result = await self.session.execute(
            select(Recipe).where(Recipe.is_active == True)
        )
        receipts = result.scalars().all()

        return [RecipeResponse.model_validate(r) for r in receipts]

    async def create_recipe(self, recipe_data: RecipeCreateRequest) -> Recipe:
        """Создание нового рецепта"""
        try:
            # Проверяем существование предмета результата
            result_item = await self.session.execute(
                select(Item).where(Item.id == recipe_data.result_item_id)
            )
            if not result_item.scalar_one_or_none():
                raise HTTPException(
                    status_code=404,
                    detail=f"Result item with id {recipe_data.result_item_id} not found",
                )

            # Проверяем существование рецепта с такими же ингредиентами
            result = await self.session.execute(select(Recipe))
            existing_recipes = result.scalars().all()

            for existing_recipe in existing_recipes:
                if self._ingredients_match(
                    existing_recipe.ingredients,
                    recipe_data.ingredients,
                ):
                    # Получаем название предмета, который крафтится
                    result_item_query = await self.session.execute(
                        select(Item).where(Item.id == existing_recipe.result_item_id)
                    )
                    result_item = result_item_query.scalar_one()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Recipe with these ingredients already exists. "
                        f"It creates: {result_item.name}",
                    )
            # Проверяем существование всех предметов-ингредиентов
            for ingredient in recipe_data.ingredients:
                item = await self.session.execute(
                    select(Item).where(Item.id == ingredient.item_id)
                )
                if not item.scalar_one_or_none():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Ingredient item with id {ingredient.item_id} not found",
                    )

            # Преобразуем ингредиенты в формат JSON для хранения
            ingredients_json = [
                {"item_id": ing.item_id, "quantity": ing.quantity}
                for ing in recipe_data.ingredients
            ]

            # Создаем новый рецепт
            recipe = Recipe(
                success_chance=recipe_data.success_chance,
                max_crafts=recipe_data.max_crafts,
                ingredients=ingredients_json,
                rarity=recipe_data.rarity,
                result_item_id=recipe_data.result_item_id,
                result_quantity=recipe_data.result_quantity,
                is_active=recipe_data.is_active,
            )

            self.session.add(recipe)
            await self.session.commit()
            await self.session.refresh(recipe)
            return recipe

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create recipe")
