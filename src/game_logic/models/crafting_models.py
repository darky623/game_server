from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class Recipe(Base):
    """Модель рецептов крафта"""
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    success_chance = Column(Float, default=75.0)  # Базовый шанс успешного крафта (75%)
    max_crafts = Column(Integer)  # Максимальное количество успешных крафтов
    is_active = Column(Boolean, default=True)
    # Список ингредиентов и их количество для крафта
    # Формат: [{"item_id": int, "quantity": int}, ...]
    ingredients = Column(JSON)
    rarity = Column(Integer)  # От 1 до 5
    result_item_id = Column(Integer, ForeignKey('items.id'))
    result_quantity = Column(Integer, default=1)

    result_item = relationship("Item")
    known_recipes = relationship("KnownRecipe", back_populates="recipe")
    craft_attempts = relationship("CraftAttempt", back_populates="recipe")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not 1 <= self.rarity <= 5:
            raise ValueError("Rarity must be between 1 and 5")
        if not isinstance(self.ingredients, list) or len(self.ingredients) > 6:
            raise ValueError("Recipe must have between 1 and 6 ingredients")


class KnownRecipe(Base):
    """Модель известных игроку рецептов"""
    __tablename__ = 'known_recipes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    # Список известных ингредиентов
    # Формат: [{"item_id": int, "quantity": int}, ...]
    known_ingredients = Column(JSON)
    current_success_chance = Column(Float)  # Базовый Шанс крафта для игрока
    # Формат: [{"booster_id": int, "bonus": float}, ...]
    applied_boosters = Column(JSON, default=[])
    is_favorite = Column(Boolean, default=False)

    recipe = relationship("Recipe", back_populates="known_recipes")
    user = relationship("User")


class CraftAttempt(Base):
    """Модель попыток крафта"""
    __tablename__ = 'craft_attempts'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    is_successful = Column(Boolean, default=False)  # True если крафт успешен или открыто >50% рецепта
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    # Использованные ингредиенты
    # Формат: [{"item_id": int, "quantity": int}, ...]
    used_ingredients = Column(JSON, nullable=True)
    success_chance = Column(Float, nullable=True)
    # Формат: [{"booster_id": int, "bonus": float}, ...]
    applied_boosters = Column(JSON, default=[])
    recipe = relationship("Recipe", back_populates="craft_attempts")
    user = relationship("User")
