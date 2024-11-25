import json

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
        ingredients: Dict[str, int],
        applied_boosters: Dict[str, int] | None = None,
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

            # Преобразуем словари в список StackBase для проверки инвентаря
            ingredients_stacks = [
                StackBase(item_id=int(item_id), quantity=quantity)
                for item_id, quantity in ingredients.items()
            ]

            # Проверяем наличие ингредиентов у пользователя
            if not await self.inventory_service.has_items(user_id, ingredients_stacks):
                raise HTTPException(
                    status_code=400, detail="Not enough ingredients in inventory"
                )

            # Ищем подходящий активный рецепт
            recipe = await self._find_matching_recipe(ingredients)
            if applied_boosters:
                boosters_stacks = [
                    StackBase(item_id=int(item_id), quantity=quantity)
                    for item_id, quantity in applied_boosters.items()
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
            await self.inventory_service.remove_items(user_id, ingredients_stacks)

            # Создаем запись о попытке крафта
            craft_attempt = CraftAttempt(
                user_id=user_id,
                recipe_id=recipe.id if recipe else None,
                used_ingredients=ingredients,
                success_chance=recipe.success_chance,
                applied_boosters=applied_boosters,
            )

            if recipe:
                # Проверяем, открыт ли частично рецепт
                known_recipe = await self._get_or_create_known_recipe(
                    user_id, recipe.id
                )
                # Обновляем известные ингредиенты
                await self._update_known_ingredients(
                    known_recipe, ingredients, recipe
                )

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
                status_code=500, detail="Database error during crafting"
            )

    async def _find_matching_recipe(
        self, ingredients: Dict[str, int]
    ) -> Optional[Recipe]:
        """Поиск подходящего рецепта по ингредиентам"""
        try:
            # Получаем все рецепты
            result = await self.session.execute(select(Recipe))
            recipes = result.scalars().all()

            for recipe in recipes:
                # Проверяем совпадение ингредиентов и их количества
                recipe_ingredients = recipe.ingredients
                if self._ingredients_match(recipe_ingredients, ingredients):
                    return recipe

            return None

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, detail="Error while searching for recipe"
            )

    def _ingredients_match(
        self, recipe_ingredients: list, provided_ingredients: dict
    ) -> bool:
        """Проверка соответствия ингредиентов рецепту"""
        if len(recipe_ingredients) != len(provided_ingredients):
            return False

        # Преобразуем список рецепта в словарь для удобства сравнения
        recipe_dict = {
            str(ing["item_id"]): ing["quantity"] for ing in recipe_ingredients
        }

        for item_id, quantity in provided_ingredients.items():
            if item_id not in recipe_dict or recipe_dict[item_id] != quantity:
                return False

        return True

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

        if not known_recipe:
            known_recipe = KnownRecipe(
                user_id=user_id,
                recipe_id=recipe_id,
                known_ingredients=None,  # Теперь это ForeignKey к Stack
                current_success_chance=75.0,
                applied_boosters=[],
            )
            self.session.add(known_recipe)
            await self.session.commit()

        return known_recipe

    async def _update_known_ingredients(
        self, known_recipe: KnownRecipe, provided_ingredients: dict, recipe: Recipe
    ) -> None:
        """Обновление известных ингредиентов рецепта"""
        recipe_ingredients = recipe.ingredients
        total_ingredients = len(recipe_ingredients)
        matched_ingredients = []

        # Находим правильно угаданные ингредиенты
        for item_id, quantity in provided_ingredients.items():
            if item_id in [
                str(ing["item_id"]) for ing in recipe_ingredients
            ] and quantity == next(
                ing["quantity"]
                for ing in recipe_ingredients
                if str(ing["item_id"]) == item_id
            ):
                # Создаем новый Stack для известных ингредиентов
                stack = Stack(item_id=int(item_id), quantity=quantity)
                self.session.add(stack)
                matched_ingredients.append(stack)

        correct_ingredients = len(matched_ingredients)
        provided_ingredients_count = len(provided_ingredients)

        # Определяем, нужно ли открывать подсказку
        should_reveal = False

        if total_ingredients == 6:
            # Для рецепта из 6 частей нужно угадать 3, 4 или 5 ингредиентов
            should_reveal = (
                provided_ingredients_count in [3, 4, 5] 
                and correct_ingredients == provided_ingredients_count
            )
        elif total_ingredients == 5:
            # Для рецепта из 5 частей нужно угадать 3 или 4 ингредиента
            should_reveal = (
                provided_ingredients_count in [3, 4] 
                and correct_ingredients == provided_ingredients_count
            )
        elif total_ingredients == 4:
            # Для рецепта из 4 частей нужно угадать минимум 3 ингредиента
            should_reveal = (
                    3 <= provided_ingredients_count == correct_ingredients
            )
        # Для рецептов из 2-3 частей подсказки не даются

        if should_reveal and matched_ingredients:
            # Если условия выполнены, сохраняем известные ингредиенты
            known_recipe.known_ingredients = matched_ingredients[0].id
            await self.session.commit()

    async def _roll_craft_success(self, known_recipe: KnownRecipe) -> bool:
        """Проверка успешности крафта с учетом шанса"""
        import random

        total_chance = known_recipe.current_success_chance
        for booster in known_recipe.applied_boosters:
            total_chance += booster.get("bonus", 0)

        return random.random() * 100 <= min(total_chance, 100)

    async def _calculate_success_chance(
        self, recipe: Recipe, applied_boosters: List[StackBase]
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
        result = await self.session.execute(select(Recipe).where(Recipe.is_active == True))
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
                    {str(ing.item_id): ing.quantity for ing in recipe_data.ingredients},
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
