import json
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

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

    def _create_ingredient_hash(self, ingredients: List[Dict]) -> str:
        """Создает уникальный хэш для комбинации ингредиентов"""
        sorted_ingredients = sorted(
            ingredients, key=lambda x: (x["item_id"], x["quantity"])
        )
        return hashlib.md5(
            json.dumps(sorted_ingredients).encode()
        ).hexdigest()

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

            # Создаем хэш ингредиентов для быстрого поиска
            ingredients_hash = self._create_ingredient_hash([
                {"item_id": ing.item_id, "quantity": ing.quantity}
                for ing in ingredients
            ])

            # Ищем подходящий активный рецепт по хэшу
            recipe = await self._find_matching_recipe(ingredients, ingredients_hash)
            
            # Проверяем и применяем бустеры
            if applied_boosters:
                recipe = await self._apply_boosters(
                    user_id, recipe, applied_boosters
                )

            # Удаляем ингредиенты из инвентаря
            await self.inventory_service.remove_items(user_id, ingredients)

            # Создаем запись о попытке крафта
            craft_attempt = await self._create_craft_attempt(
                user_id, recipe, ingredients, applied_boosters
            )

            if recipe:
                # Получаем или создаем запись об известном рецепте
                known_recipe = await self._get_or_create_known_recipe(
                    user_id, recipe.id
                )
                
                # Обновляем известные ингредиенты и прогресс
                await self._update_known_ingredients(
                    user_id, recipe, ingredients
                )

                # Проверяем возможность крафта
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
                status_code=500, detail=f"Database error during crafting: {str(e)}"
            )

    async def _find_matching_recipe(
        self, ingredients: List[StackBase], ingredients_hash: str
    ) -> Optional[Recipe]:
        """Поиск подходящего рецепта по ингредиентам и хэшу"""
        try:
            # Сначала ищем по хэшу для оптимизации
            result = await self.session.execute(
                select(Recipe).where(
                    and_(
                        Recipe.ingredient_hash == ingredients_hash,
                        Recipe.is_active == True
                    )
                )
            )
            recipe = result.scalar_one_or_none()
            
            if recipe:
                return recipe

            # Если по хэшу не нашли, проверяем все активные рецепты
            result = await self.session.execute(
                select(Recipe).where(Recipe.is_active == True)
            )
            recipes = result.scalars().all()

            for recipe in recipes:
                if self._ingredients_full_match(recipe.ingredients, ingredients):
                    return recipe

            return None

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, detail="Error while searching for recipe"
            )

    def _ingredients_full_match(
        self, recipe_ingredients: List[Dict], provided_ingredients: List[StackBase]
    ) -> bool:
        """Проверка точного соответствия ингредиентов рецепту"""
        recipe_dict = {
            ing["item_id"]: ing["quantity"] for ing in recipe_ingredients
        }
        provided_dict = {
            ing.item_id: ing.quantity for ing in provided_ingredients
        }

        # Проверяем наличие всех необходимых ингредиентов
        for item_id, required_qty in recipe_dict.items():
            if (
                item_id not in provided_dict
                or provided_dict[item_id] < required_qty
            ):
                return False

        return True

    def _should_reveal_recipe(
        self, total_ingredients: int, correct_ingredients: int
    ) -> bool:
        """Определяет, нужно ли открывать часть рецепта"""
        # Для любого количества ингредиентов
        return correct_ingredients > total_ingredients / 2

    async def _update_known_ingredients(
        self,
        user_id: int,
        recipe: Recipe,
        provided_ingredients: List[StackBase],
    ):
        """Обновляет известные ингредиенты в KnownRecipe"""
        known_recipe = await self._get_or_create_known_recipe(
            user_id, recipe.id
        )

        matched_ingredients = []
        correct_ingredients = 0
        
        # Проверяем каждый предоставленный ингредиент
        for provided in provided_ingredients:
            for recipe_ing in recipe.ingredients:
                if provided.item_id == recipe_ing["item_id"]:
                    exact_match = provided.quantity == recipe_ing["quantity"]
                    matched_ingredients.append({
                        "item_id": provided.item_id,
                        "quantity": provided.quantity,
                        "exact_match": exact_match
                    })
                    if exact_match:
                        correct_ingredients += 1
                    break

        total_ingredients = len(recipe.ingredients)
        
        # Проверяем, нужно ли открывать часть рецепта
        if self._should_reveal_recipe(total_ingredients, correct_ingredients):
            current_known = known_recipe.known_ingredients or {
                "matched": [],
                "total_required": total_ingredients,
                "discovery_progress": 0
            }

            # Обновляем прогресс открытия
            new_ingredients = [
                ing for ing in matched_ingredients
                if ing not in current_known["matched"]
            ]
            current_known["matched"].extend(new_ingredients)
            current_known["discovery_progress"] = (
                len(current_known["matched"]) / total_ingredients
            ) * 100

            known_recipe.known_ingredients = current_known
            known_recipe.last_craft_attempt = datetime.now()
            await self.session.commit()

    async def _create_craft_attempt(
        self,
        user_id: int,
        recipe: Optional[Recipe],
        ingredients: List[StackBase],
        applied_boosters: Optional[List[StackBase]] = None,
    ) -> CraftAttempt:
        """Создает запись о попытке крафта"""
        used_ingredients = {
            "ingredients": [
                {"item_id": ing.item_id, "quantity": ing.quantity}
                for ing in ingredients
            ],
            "matched_recipe_parts": 0,
            "total_recipe_parts": 0
        }

        if recipe:
            matched_parts = sum(
                1 for ing in ingredients
                if any(
                    ring["item_id"] == ing.item_id
                    and ring["quantity"] == ing.quantity
                    for ring in recipe.ingredients
                )
            )
            used_ingredients.update({
                "matched_recipe_parts": matched_parts,
                "total_recipe_parts": len(recipe.ingredients)
            })

        return CraftAttempt(
            user_id=user_id,
            recipe_id=recipe.id if recipe else None,
            used_ingredients=used_ingredients,
            success_chance=recipe.success_chance if recipe else None,
            applied_boosters=[
                {"booster_id": b.item_id, "bonus": b.quantity}
                for b in (applied_boosters or [])
            ]
        )

    async def _apply_boosters(
        self,
        user_id: int,
        recipe: Recipe,
        boosters: List[StackBase]
    ) -> Recipe:
        """Применяет бустеры к рецепту"""
        if not await self.inventory_service.has_items(user_id, boosters):
            raise HTTPException(
                status_code=400,
                detail="Not enough boosters in inventory"
            )

        await self.inventory_service.remove_items(user_id, boosters)
        
        total_bonus = sum(
            booster.quantity for booster in boosters
        )
        recipe.success_chance = min(
            recipe.success_chance + total_bonus,
            99.0
        )
        
        return recipe

    @cache(expire=3600)
    async def get_all_active_recipes(self) -> List[Recipe]:
        """Получение всех активных рецептов игры"""
        result = await self.session.execute(
            select(Recipe)
            .where(Recipe.is_active == True)
            .order_by(Recipe.rarity)
        )
        return result.scalars().all()

    async def create_recipe(self, recipe_data: RecipeCreateRequest) -> Recipe:
        """Создание нового рецепта"""
        try:
            ingredients_hash = self._create_ingredient_hash(
                recipe_data.ingredients
            )
            
            recipe = Recipe(
                ingredients=recipe_data.ingredients,
                result_item_id=recipe_data.result_item_id,
                result_quantity=recipe_data.result_quantity,
                rarity=recipe_data.rarity,
                max_crafts=recipe_data.max_crafts,
                success_chance=recipe_data.success_chance or 75.0,
                ingredient_hash=ingredients_hash
            )
            
            self.session.add(recipe)
            await self.session.commit()
            return recipe
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating recipe: {str(e)}"
            )
