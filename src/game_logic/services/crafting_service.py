from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict

from src.game_logic.models.crafting_models import Recipe, KnownRecipe, CraftAttempt
from src.game_logic.models.inventory_models import Item, Stack
from src.game_logic.schemas.inventory_schemas import StackBase
from src.game_logic.services.service import Service
from src.game_logic.services.inventory_service import InventoryService


class CraftingService(Service):
    inventory_service: InventoryService

    def __init__(self, session):
        super().__init__(session)
        self.inventory_service = InventoryService(session)

    async def attempt_craft(self, user_id: int, ingredients: List[StackBase],
                            applied_boosters: List[StackBase] | None = None) -> dict:
        """
        Попытка крафта предметов. Игрок может отправить от 1 до 6 ингредиентов.
        Если найден подходящий рецепт и крафт успешен - игрок получает предмет.
        Ингредиенты тратятся в любом случае.
        """
        try:
            if not ingredients or len(ingredients) > 6:
                raise HTTPException(
                    status_code=400,
                    detail="Number of ingredients must be between 1 and 6"
                )

            # Проверяем наличие ингредиентов у пользователя
            if not await self.inventory_service.has_items(user_id, ingredients):
                raise HTTPException(
                    status_code=400,
                    detail="Not enough ingredients in inventory"
                )

            # Преобразуем ингредиенты в формат для поиска рецепта
            ingredients_dict = {str(ing.item_id): ing.quantity for ing in ingredients}

            # Ищем подходящий активный рецепт
            recipe = await self._find_matching_recipe(ingredients_dict)

            if applied_boosters:
                # Проверяем действительно ли игрока есть те бустеры, которые он применяет
                applied_boosters = await self.inventory_service.has_items(user_id, applied_boosters)
                # Если не бонусы не в инвентаре возвращаем ошибку
                if not applied_boosters:
                    raise HTTPException(
                        status_code=400,
                        detail="No matching recipe or boosters not found"
                    )
            # Удаляем ингредиенты из инвентаря (они тратятся в любом случае)
            await self.inventory_service.remove_items(user_id, ingredients)
            await self.inventory_service.remove_items(user_id, applied_boosters)
            success_chance = self._calculate_success_chance(recipe, applied_boosters)
            # Создаем запись о попытке крафта
            craft_attempt = CraftAttempt(
                user_id=user_id,
                recipe_id=recipe.id if recipe else None,
                used_ingredients=ingredients_dict,
                is_successful=True if recipe else False,
                success_chance=success_chance,
                applied_boosters=applied_boosters
            )

            if recipe:
                # Проверяем, открыт ли частично рецепт
                known_recipe = await self._get_or_create_known_recipe(user_id, recipe.id)

                # Обновляем известные ингредиенты
                await self._update_known_ingredients(known_recipe, ingredients_dict, recipe)

                # Если рецепт найден и активен, проверяем шанс успеха
                if recipe.is_active and await self._roll_craft_success(known_recipe):
                    # Крафт успешен
                    craft_attempt.is_successful = True
                    await self.inventory_service.add_items_to_inventory(
                        user_id,
                        [StackBase(item_id=recipe.result_item_id, quantity=recipe.result_quantity)]
                    )

                    return {
                        "success": True,
                        "message": "Crafting successful!",
                        "crafted_item_id": recipe.result_item_id,
                        "quantity": recipe.result_quantity
                    }

            # Сохраняем попытку крафта
            self.session.add(craft_attempt)
            await self.session.commit()

            if not recipe:
                return {
                    "success": False,
                    "message": "No matching recipe found"
                }

            return {
                "success": False,
                "message": "Crafting failed"
            }

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail="Database error during crafting")

    async def _find_matching_recipe(self, ingredients: Dict[str, int]) -> Optional[Recipe]:
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
            raise HTTPException(status_code=500, detail="Error while searching for recipe")

    def _ingredients_match(self, recipe_ingredients: list, provided_ingredients: dict) -> bool:
        """Проверка соответствия ингредиентов рецепту"""
        if len(recipe_ingredients) != len(provided_ingredients):
            return False

        # Преобразуем список рецепта в словарь для удобства сравнения
        recipe_dict = {str(ing['item_id']): ing['quantity'] for ing in recipe_ingredients}

        for item_id, quantity in provided_ingredients.items():
            if (
                    item_id not in recipe_dict
                    or recipe_dict[item_id] != quantity
            ):
                return False

        return True

    async def _get_or_create_known_recipe(self, user_id: int, recipe_id: int) -> KnownRecipe:
        """Получение или создание записи об известном рецепте"""
        result = await self.session.execute(
            select(KnownRecipe).where(
                KnownRecipe.user_id == user_id,
                KnownRecipe.recipe_id == recipe_id
            )
        )
        known_recipe = result.scalar_one_or_none()

        if not known_recipe:
            known_recipe = KnownRecipe(
                user_id=user_id,
                recipe_id=recipe_id,
                known_ingredients=None,  # Теперь это ForeignKey к Stack
                current_success_chance=75.0,
                applied_boosters=[]
            )
            self.session.add(known_recipe)
            await self.session.commit()

        return known_recipe

    async def _update_known_ingredients(
            self,
            known_recipe: KnownRecipe,
            provided_ingredients: dict,
            recipe: Recipe
    ) -> None:
        """Обновление известных ингредиентов рецепта"""
        recipe_ingredients = recipe.ingredients
        total_ingredients = len(recipe_ingredients)
        matched_ingredients = []

        # Находим правильно угаданные ингредиенты
        for item_id, quantity in provided_ingredients.items():
            if item_id in [str(ing['item_id']) for ing in recipe_ingredients] and \
                    quantity == next(ing['quantity'] for ing in recipe_ingredients if str(ing['item_id']) == item_id):
                # Создаем новый Stack для известных ингредиентов
                stack = Stack(
                    item_id=int(item_id),
                    quantity=quantity
                )
                self.session.add(stack)
                matched_ingredients.append(stack)

        # Если угадано больше половины ингредиентов
        if len(matched_ingredients) >= total_ingredients / 2:
            await self.session.flush()  # Чтобы получить id нового Stack
            known_recipe.known_ingredients = matched_ingredients[0].id  # Сохраняем id первого стека
            await self.session.commit()

    async def _roll_craft_success(self, known_recipe: KnownRecipe) -> bool:
        """Проверка успешности крафта с учетом шанса"""
        import random

        total_chance = known_recipe.current_success_chance
        for booster in known_recipe.applied_boosters:
            total_chance += booster.get('bonus', 0)

        return random.random() * 100 <= min(total_chance, 100)

    async def _calculate_success_chance(self, recipe: Recipe, applied_boosters: List[StackBase]) -> float:
        """Вычисление шанса крафта с учетом примененных усилителей"""
        total_chance = recipe.success_chance
        for booster in applied_boosters:
            total_chance += booster.get('bonus', 0)

        return total_chance

    async def get_known_recipes(self, user_id: int) -> List[KnownRecipe]:
        """Получение всех известных рецептов пользователя"""
        result = await self.session.execute(
            select(KnownRecipe)
            .options(joinedload(KnownRecipe.recipe))
            .where(KnownRecipe.user_id == user_id)
        )
        return result.scalars().all()

    async def toggle_recipe_favorite(self, user_id: int, recipe_id: int) -> KnownRecipe:
        """Добавление/удаление рецепта из избранного"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)
        known_recipe.is_favorite = not known_recipe.is_favorite
        await self.session.commit()
        return known_recipe

    async def apply_booster(self, user_id: int, recipe_id: int, booster_id: int, bonus: float) -> KnownRecipe:
        """Применение усилителя к рецепту"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)

        # Проверяем, не применен ли уже такой бустер
        for booster in known_recipe.applied_boosters:
            if booster['booster_id'] == booster_id:
                raise HTTPException(400, "This booster is already applied")

        known_recipe.applied_boosters.append({
            'booster_id': booster_id,
            'bonus': bonus
        })

        await self.session.commit()
        return known_recipe
