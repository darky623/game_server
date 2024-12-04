import json
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Any

from fastapi import HTTPException
from sqlalchemy import select, and_, Row, RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.game_logic.models.crafting_models import Recipe, KnownRecipe, CraftAttempt
from cache.client import cache_service
from src.game_logic.models.inventory_models import Item
from src.game_logic.schemas.crafting_schemas import (
    RecipeCreateRequest,
    KnownRecipeResponse,
    RecipeResponse,
    CraftAttemptResponse,
    DiscoveredRecipeInfo
)
from src.game_logic.schemas.inventory_schemas import StackBase, StackResponse
from src.game_logic.services.service import Service
from src.game_logic.services.inventory_service import InventoryService


class CraftingService(Service):
    inventory_service: InventoryService

    def __init__(self, session):
        super().__init__(session)
        self.inventory_service = InventoryService(session)

    def _create_ingredient_hash(self, ingredients: List[StackBase]) -> str:
        """Создает хеш для списка ингредиентов"""
        sorted_ingredients = sorted(
            ingredients, key=lambda x: (x.item_id, x.quantity)
        )
        ingredients_str = json.dumps([
            {"item_id": ing.item_id, "quantity": ing.quantity}
            for ing in sorted_ingredients
        ])
        return hashlib.md5(ingredients_str.encode()).hexdigest()

    async def attempt_craft(
        self,
        user_id: int,
        ingredients: List[StackBase],
        applied_boosters: List[StackBase] | None = None,
        craft_count: int = 1
    ) -> CraftAttemptResponse:
        """
        Попытка крафта предметов. Игрок может отправить от 1 до 6 ингредиентов.
        Если найден подходящий рецепт и крафт успешен - игрок получает предмет.
        Ингредиенты тратятся в любом случае.
        """
        if not ingredients:
            raise HTTPException(
                status_code=400, detail="No ingredients provided"
            )

        if len(ingredients) > 6:
            raise HTTPException(
                status_code=400, detail="Too many ingredients (max 6)"
            )

        if applied_boosters and len(applied_boosters) > 3:
            raise HTTPException(
                status_code=400, detail="Too many boosters (max 3)"
            )

        try:
            # Проверяем наличие ингредиентов в инвентаре
            if not await self.inventory_service.has_items(user_id, ingredients):
                raise HTTPException(
                    status_code=400, detail="Not enough ingredients"
                )

            # Создаем хэш ингредиентов для быстрого поиска
            ingredients_hash = self._create_ingredient_hash(ingredients)

            discovered_recipes: List[DiscoveredRecipeInfo] = []
            recipe = None
            
            # Ищем подходящий активный рецепт по хэшу
            recipe = await self._find_matching_recipe(ingredients, ingredients_hash, user_id, discovered_recipes)

            # Если рецепт не найден
            if not recipe:
                await self._create_craft_attempt(
                    user_id, None, ingredients, applied_boosters
                )
                
                if discovered_recipes:
                    return CraftAttemptResponse(
                        success=False,
                        discovered_recipes=discovered_recipes,
                        message="Recipe not found, but you discovered some new recipes!",
                        used_ingredients=[{"item_id": ing.item_id, "quantity": ing.quantity} for ing in ingredients],
                        used_boosters=[{"item_id": b.item_id, "quantity": b.quantity} for b in (applied_boosters or [])],
                        discovery_mode=True
                    )
                return CraftAttemptResponse(
                    success=False,
                    message="Recipe not found",
                    used_ingredients=[{"item_id": ing.item_id, "quantity": ing.quantity} for ing in ingredients],
                    used_boosters=[{"item_id": b.item_id, "quantity": b.quantity} for b in (applied_boosters or [])],
                    discovery_mode=True
                )

            # Получаем информацию об известном рецепте
            known_recipe = await self._get_or_create_known_recipe(
                user_id, recipe.id
            )

            # Применяем бустеры только к текущей попытке
            booster_bonus = 0
            used_boosters = []
            if applied_boosters:
                booster_bonus, used_boosters = await self._apply_boosters(
                    user_id, recipe, applied_boosters
                )

            # Удаляем ингредиенты из инвентаря
            await self.inventory_service.remove_items(user_id, ingredients)

            # Проверяем успешность крафта с учетом временных бустеров
            craft_chance = await self._calculate_craft_chance(known_recipe, booster_bonus)
            if not await self._roll_craft_success(known_recipe):
                await self._create_craft_attempt(
                    user_id, recipe, ingredients, applied_boosters
                )
                return CraftAttemptResponse(
                    success=False,
                    discovered_recipes=discovered_recipes,
                    message="Craft failed - better luck next time!",
                    used_ingredients=[{"item_id": ing.item_id, "quantity": ing.quantity} for ing in ingredients],
                    used_boosters=[{"item_id": b.item_id, "quantity": b.quantity} for b in (applied_boosters or [])],
                    recipe_id=recipe.id,
                    craft_chance=craft_chance
                )

            # Добавляем предмет в инвентарь
            await self.inventory_service.add_items_to_inventory(
                user_id,
                [
                    StackBase(
                        item_id=recipe.result_item_id,
                        quantity=recipe.result_quantity * craft_count,
                    )
                ],
            )

            # Создаем запись об успешной попытке
            await self._create_craft_attempt(
                user_id, recipe, ingredients, applied_boosters, True
            )

            return CraftAttemptResponse(
                success=True,
                crafted_item_id=recipe.result_item_id,
                crafted_quantity=recipe.result_quantity * craft_count,
                discovered_recipes=discovered_recipes,
                message="Craft successful!",
                used_ingredients=[{"item_id": ing.item_id, "quantity": ing.quantity} for ing in ingredients],
                used_boosters=[{"item_id": b.item_id, "quantity": b.quantity} for b in (applied_boosters or [])],
                recipe_id=recipe.id,
                craft_chance=craft_chance
            )

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500, detail=f"Database error: {str(e)}"
            )

    async def _find_matching_recipe(
        self, ingredients: List[StackBase], ingredients_hash: str, user_id: int,
        discovered_recipes: List[DiscoveredRecipeInfo]
    ) -> Optional[Recipe]:
        """Поиск подходящего рецепта по ингредиентам и хэшу"""
        try:
            # Сначала ищем по хэшу для оптимизации
            result = await self.session.execute(
                select(Recipe).where(
                    and_(
                        Recipe.ingredient_hash == ingredients_hash,
                        Recipe.is_active == True,
                        Recipe.is_secret == False
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

            # Проверяем полное совпадение
            for recipe in recipes:
                if self._ingredients_full_match(recipe.ingredients, ingredients):
                    return recipe

            # Если не нашли полного совпадения, проверяем частичные совпадения
            for recipe in recipes:
                matched_ingredients = self._get_matched_ingredients(recipe.ingredients, ingredients)
                total_ingredients = len(recipe.ingredients)
                matched_count = len(matched_ingredients)

                # Если отгадано больше половины ингредиентов
                if matched_count / total_ingredients >= 0.5:
                    # Обновляем известные ингредиенты для этого рецепта
                    known_recipe = await self._update_known_ingredients(user_id, recipe, ingredients)
                    
                    # Добавляем информацию об отгаданном рецепте
                    discovered_recipes.append(DiscoveredRecipeInfo(
                        recipe_id=recipe.id,
                        result_item_id=recipe.result_item_id,
                        discovery_progress=known_recipe.known_ingredients["discovery_progress"],
                        known_ingredients=known_recipe.known_ingredients["matched"]
                    ))

            return None

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, detail="Error while searching for recipe"
            )

    async def _update_known_ingredients(
        self,
        user_id: int,
        recipe: Recipe,
        provided_ingredients: List[StackBase],
    ) -> KnownRecipe:
        """Обновляет известные ингредиенты в KnownRecipe"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe.id)
        
        # Получаем текущие известные ингредиенты
        current_known = known_recipe.known_ingredients.get("matched", []) if known_recipe.known_ingredients else []
        current_known_dict = {ing["item_id"]: ing for ing in current_known}
        
        # Находим совпадающие ингредиенты в текущей попытке
        new_matches = self._get_matched_ingredients(recipe.ingredients, provided_ingredients)
        
        # Обновляем информацию об известных ингредиентах
        for match in new_matches:
            item_id = match["item_id"]
            if item_id not in current_known_dict:
                # Добавляем новый отгаданный ингредиент
                current_known.append(match)
            elif not current_known_dict[item_id]["exact_match"] and match["exact_match"]:
                # Обновляем если нашли точное совпадение для ранее неточно отгаданного ингредиента
                current_known_dict[item_id].update(match)

        # Обновляем прогресс открытия рецепта
        total_ingredients = len(recipe.ingredients)
        matched_count = len(current_known)
        discovery_progress = matched_count / total_ingredients

        known_recipe.known_ingredients = {
            "matched": current_known,
            "total_required": total_ingredients,
            "discovery_progress": discovery_progress
        }

        await self.session.commit()
        return known_recipe

    def _get_matched_ingredients(
        self, recipe_ingredients: List[Dict], provided_ingredients: List[StackBase]
    ) -> List[Dict]:
        """Находит совпадающие ингредиенты между рецептом и предоставленными ингредиентами"""
        matched = []
        recipe_dict = {
            ing["item_id"]: ing["quantity"] for ing in recipe_ingredients
        }
        provided_dict = {
            ing.item_id: ing.quantity for ing in provided_ingredients
        }

        for ing in recipe_ingredients:
            item_id = ing["item_id"]
            if item_id in provided_dict:
                # Проверяем точное совпадение количества
                if provided_dict[item_id] == ing["quantity"]:
                    matched.append({
                        "item_id": item_id,
                        "quantity": ing["quantity"],
                        "exact_match": True
                    })
                else:
                    # Ингредиент угадан, но количество неверное
                    matched.append({
                        "item_id": item_id,
                        "quantity": ing["quantity"],
                        "exact_match": False
                    })

        return matched

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
                or provided_dict[item_id] != required_qty  # Изменено с < на != для точного совпадения
            ):
                return False

        # Проверяем, что нет лишних ингредиентов
        return len(recipe_dict) == len(provided_dict)

    async def _create_craft_attempt(
        self,
        user_id: int,
        recipe: Optional[Recipe],
        ingredients: List[StackBase],
        applied_boosters: Optional[List[StackBase]] = None,
        is_successful: bool = False,
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
            ],
            is_successful=is_successful
        )

    async def _apply_boosters(
        self,
        user_id: int,
        recipe: Recipe,
        boosters: List[StackBase]
    ) -> Tuple[float, List[Dict]]:
        """
        Применяет бустеры к текущей попытке крафта.
        Возвращает бонус к шансу крафта и список примененных бустеров.
        """
        if not await self.inventory_service.has_items(user_id, boosters):
            raise HTTPException(
                status_code=400,
                detail="Not enough boosters in inventory"
            )

        # Получаем информацию о каждом бустере
        booster_items = []
        for booster in boosters:
            item = await self.session.execute(
                select(Item).where(Item.id == booster.item_id)
            )
            item = item.scalar_one_or_none()
            if not item or not item.item_data or item.item_data.get('type') != 'craft_booster':
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {booster.item_id} is not a valid crafting booster"
                )
            booster_items.append((item, booster.quantity))

        # Тратим бустеры
        await self.inventory_service.remove_items(user_id, boosters)

        # Считаем общий бонус и собираем информацию о примененных бустерах
        total_bonus = 0
        applied_boosters = []
        for item, quantity in booster_items:
            bonus = item.item_data.get('bonus', 0)
            for _ in range(quantity):
                total_bonus += bonus
                applied_boosters.append({
                    "booster_id": item.id,
                    "bonus": bonus
                })

        return total_bonus, applied_boosters

    async def _calculate_craft_chance(
        self, 
        known_recipe: KnownRecipe,
        booster_bonus: float = 0
    ) -> float:
        """Рассчитывает шанс крафта с учетом временных бустеров"""
        # Получаем базовый шанс из рецепта
        recipe = await self.session.execute(
            select(Recipe).where(Recipe.id == known_recipe.recipe_id)
        )
        recipe = recipe.scalar_one()
        
        # Добавляем бонус от временных бустеров
        total_chance = recipe.success_chance + booster_bonus

        # Ограничиваем максимальный шанс до 99%
        return min(total_chance, 99.0)

    async def get_all_recipes(self) -> List[Recipe]:
        """Получение всех активных рецептов"""
        result = await self.session.execute(
            select(Recipe).where(
                and_(
                    Recipe.is_active == True,
                    Recipe.is_secret == False
                )
            )
        )
        return list(result.scalars().all())

    async def get_recipe(self, recipe_id: int, user_id: int = None) -> Optional[Recipe]:
        """Получение рецепта по ID"""
        query = select(Recipe).where(Recipe.id == recipe_id)
        
        # Для секретных рецептов проверяем, знает ли пользователь хотя бы часть ингредиентов
        if user_id:
            known_recipe = await self.session.execute(
                select(KnownRecipe).where(
                    KnownRecipe.recipe_id == recipe_id,
                    KnownRecipe.user_id == user_id
                )
            )
            known_recipe = known_recipe.scalar_one_or_none()
            
            if known_recipe and known_recipe.known_ingredients:
                result = await self.session.execute(query)
                return result.scalar_one_or_none()
            
            # Если рецепт секретный и пользователь не знает ингредиентов, возвращаем None
            recipe = await self.session.execute(query)
            recipe = recipe.scalar_one_or_none()
            if recipe and recipe.is_secret:
                return None
        
        result = await self.session.execute(query)
        recipe = result.scalar_one_or_none()
        return recipe

    async def get_known_recipes(self, user_id: int) -> List[KnownRecipe]:
        """Получение всех известных рецептов пользователя"""
        known_recipes = await self.session.execute(
            select(KnownRecipe)
            .where(KnownRecipe.user_id == user_id)
            .options(joinedload(KnownRecipe.recipe))
        )

        krs = known_recipes.scalars().all()

        return list(krs)

    async def create_recipe(self, recipe_data: RecipeCreateRequest) -> Recipe:
        """Создание нового рецепта"""
        try:
            ingredients_hash = self._create_ingredient_hash(recipe_data.ingredients)
            
            # Преобразуем StackBase в словари для сохранения в JSON
            ingredients_dict = [
                {"item_id": ing.item_id, "quantity": ing.quantity}
                for ing in recipe_data.ingredients
            ]
            
            recipe = Recipe(
                ingredients=ingredients_dict,
                result_item_id=recipe_data.result_item_id,
                rarity=recipe_data.rarity,
                max_crafts=recipe_data.max_crafts,
                result_quantity=recipe_data.result_quantity,
                success_chance=recipe_data.success_chance,
                ingredient_hash=ingredients_hash,
                is_active=recipe_data.is_active,
                is_secret=recipe_data.is_secret
            )
            
            self.session.add(recipe)
            await self.session.commit()
            await self.session.refresh(recipe)
            
            return recipe
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating recipe: {str(e)}"
            )

    async def update_recipe(
        self,
        recipe_id: int,
        success_chance: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Recipe]:
        """Обновляет параметры рецепта"""
        # Находим рецепт
        recipe = await self.get_recipe(recipe_id)
        if not recipe:
            return None

        if success_chance is not None:
            recipe.success_chance = success_chance
        if is_active is not None:
            recipe.is_active = is_active

        await self.session.commit()
        await self.session.refresh(recipe)
        return recipe

    @staticmethod
    async def _roll_craft_success(known_recipe: KnownRecipe) -> bool:
        """Проверка успешности крафта с учетом шанса"""
        import random

        total_chance = known_recipe.current_success_chance
        if known_recipe.applied_boosters:
            for booster in known_recipe.applied_boosters:
                if booster.get("expires_at"):
                    # Проверяем, не истек ли срок действия бустера
                    expires_at = datetime.fromisoformat(booster["expires_at"])
                    if expires_at > datetime.now():
                        total_chance += booster.get("bonus", 0)
                else:
                    total_chance += booster.get("bonus", 0)

        return random.random() * 100 <= min(total_chance, 99)

    async def _get_or_create_known_recipe(
        self, user_id: int, recipe_id: int
    ) -> KnownRecipe:
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
                known_ingredients={
                    "matched": [],
                    "total_required": 0,
                    "discovery_progress": 0
                },
                current_success_chance=75.0,
                applied_boosters=[],
                last_craft_attempt=datetime.now()
            )
            self.session.add(known_recipe)
            await self.session.commit()

        return known_recipe

    async def _update_known_recipe(
        self,
        user_id: int,
        recipe_id: int,
        discovered_ingredients: List[Dict[str, Any]]
    ) -> None:
        """Обновляет известные ингредиенты рецепта для пользователя"""
        known_recipe = await self.session.execute(
            select(KnownRecipe).where(
                KnownRecipe.user_id == user_id,
                KnownRecipe.recipe_id == recipe_id
            )
        )
        known_recipe = known_recipe.scalar_one_or_none()

        if known_recipe:
            # Обновляем список известных ингредиентов
            current_ingredients = known_recipe.known_ingredients or []
            new_ingredients = []
            
            # Добавляем только уникальные ингредиенты
            seen_ingredients = {(i["item_id"], i["quantity"]) for i in current_ingredients}
            for ingredient in discovered_ingredients:
                key = (ingredient["item_id"], ingredient["quantity"])
                if key not in seen_ingredients:
                    new_ingredients.append(ingredient)
                    seen_ingredients.add(key)
            
            known_recipe.known_ingredients = current_ingredients + new_ingredients
        else:
            # Создаем новую запись
            known_recipe = KnownRecipe(
                user_id=user_id,
                recipe_id=recipe_id,
                current_success_chance=75.0,  # Базовый шанс
                known_ingredients=discovered_ingredients
            )
            self.session.add(known_recipe)

        await self.session.commit()

    async def _ingredients_match(self, ingredients: List[StackBase]) -> List[Optional[Recipe]]:
        """
        Проверяет совпадения ингредиентов с рецептами в базе данных.
        Возвращает список рецептов, которые частично доступны игроку.
        """
        ingredient_counts = defaultdict(int)
        for ing in ingredients:
            ingredient_counts[ing.item_id] += ing.quantity

        result = await self.session.execute(
            select(Recipe).where(Recipe.is_active == True)
        )
        recipes = result.scalars().all()

        available_recipes = []
        for recipe in recipes:
            matching_ingredients = 0
            missing_ingredients = []

            for ingredient in recipe.ingredients:
                if ingredient["item_id"] in ingredient_counts:
                    if ingredient_counts[ingredient["item_id"]] >= ingredient["quantity"]:
                        matching_ingredients += 1
                    else:
                        missing_ingredients.append({
                            "item_id": ingredient["item_id"],
                            "quantity": ingredient["quantity"] - ingredient_counts[ingredient["item_id"]]
                        })
                else:
                    missing_ingredients.append({
                        "item_id": ingredient["item_id"],
                        "quantity": ingredient["quantity"]
                    })

            if matching_ingredients > 0:
                recipe.ingredients = missing_ingredients
                available_recipes.append(recipe)

        return available_recipes

    async def toggle_recipe_favorite(self, user_id: int, recipe_id: int) -> KnownRecipe:
        """Добавление/удаление рецепта из избранного"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)
        known_recipe.is_favorite = not known_recipe.is_favorite
        await self.session.commit()
        return known_recipe

    async def apply_booster(
        self, user_id: int, recipe_id: int, booster_id: int, bonus: float,
        duration_hours: Optional[int] = None
    ):
        """Применение усилителя к рецепту"""
        known_recipe = await self._get_or_create_known_recipe(user_id, recipe_id)

        # Проверяем, не применен ли уже такой бустер
        for booster in known_recipe.applied_boosters:
            if booster["booster_id"] == booster_id:
                if booster.get("expires_at"):
                    expires_at = datetime.fromisoformat(booster["expires_at"])
                    if expires_at > datetime.now():
                        raise HTTPException(400, "This booster is already active")
                else:
                    raise HTTPException(400, "This booster is already applied")

        booster_data = {"booster_id": booster_id, "bonus": bonus}
        if duration_hours:
            booster_data["expires_at"] = (
                datetime.now() + timedelta(hours=duration_hours)
            ).isoformat()

        if not known_recipe.applied_boosters:
            known_recipe.applied_boosters = []
        known_recipe.applied_boosters.append(booster_data)

        await self.session.commit()
        return known_recipe

    async def share_recipe(self, user_id: int, recipe_id: int, target_user_ids: List[int]) -> KnownRecipeResponse:
        """
        Поделиться рецептом с другим игроком.
        
        Args:
            user_id: ID пользователя, который делится рецептом
            recipe_id: ID рецепта
            target_user_id: ID пользователей, которым передается рецепт
            
        Returns:
            bool: True если рецепт успешно передан, False если возникла ошибка
            
        Raises:
            HTTPException: если рецепт не найден, является секретным или пользователи не в одном клане
        """
        try:

            # Проверяем существование рецепта и что он известен пользователю
            known_recipe = await self.session.execute(
                select(KnownRecipe)
                .where(
                    and_(
                        KnownRecipe.user_id == user_id,
                        KnownRecipe.recipe_id == recipe_id
                    )
                )
                .options(joinedload(KnownRecipe.recipe))
            )
            known_recipe = known_recipe.scalar_one_or_none()
            
            if not known_recipe:
                raise HTTPException(
                    status_code=404,
                    detail="Recipe not found or not known to user"
                )
                
            # Проверяем, что рецепт не является секретным
            if known_recipe.recipe.is_secret:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot share secret recipes"
                )
                
            # TODO: Добавить проверку, что пользователи находятся в одном клане
            shared_recipe = KnownRecipeResponse.model_validate(known_recipe)
            return shared_recipe
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to share recipe"
            )
