import asyncio
import hashlib
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.game_logic.models.crafting_models import Recipe


def create_ingredient_hash(ingredients: list) -> str:
    """Создает уникальный хэш для комбинации ингредиентов"""
    sorted_ingredients = sorted(
        ingredients,
        key=lambda x: (x["item_id"], x["quantity"])
    )
    return hashlib.md5(
        json.dumps(sorted_ingredients).encode()
    ).hexdigest()


async def update_existing_recipes():
    """Обновляет существующие рецепты, добавляя хэши ингредиентов"""
    async with AsyncSession() as session:
        try:
            # Получаем все рецепты
            result = await session.execute(select(Recipe))
            recipes = result.scalars().all()
            
            updated_count = 0
            for recipe in recipes:
                if not recipe.ingredient_hash:
                    recipe.ingredient_hash = create_ingredient_hash(recipe.ingredients)
                    updated_count += 1
            
            await session.commit()
            print(f"Successfully updated {updated_count} recipes")
            
        except Exception as e:
            print(f"Error updating recipes: {str(e)}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_existing_recipes())
