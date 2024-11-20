from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, orm, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


from config.database import Base


class Resource(Base):
    """ Один ресурс в игре.
    Класс для ресурсов, которые могут быть предметами или вещами."""
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    rarity = Column(String)
    stackable = Boolean(True)
    icon = Column(String)


class Inventory(Base):
    """ Инвентарь игрока.
    Класс для хранения предметов игрока."""
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey('players.id'))  # Предполагается, что игроки хранятся в таблице players
    stacks = relationship("Stack", back_populates="inventory")


class Stack(Base):
    """ Стэк предметов.
    Класс для хранения нескольких экземпляров одного ресурса в инвентаре."""
    __tablename__ = 'stacks'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id'))
    inventory_id = Column(Integer, ForeignKey('inventories.id'))
    quantity = Column(Integer)

    resource = relationship("Resource")
    inventory = relationship("Inventory", back_populates="stacks")


class Item(Base):
    """ Предмет игрока.
    Класс для хранения информации о предметах игрока(в инвентаре)."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    stack_id = Column(Integer, ForeignKey('stacks.id'))
    stack = relationship("Stack")

    is_stacked = Boolean()

    item_type = Column(Enum("equipment", "runes", "consumables", "quest_items"))  # Например, 'снаряжение', 'руны', 'расходники', 'квестовые предметы'
    item_data = Column(JSONB)  # Данные о предмете, например, для снаряжения - характеристики, для рун - силы и т.д.

    name = Column(String)
    level = Column(Integer)  # Можно хранить в item_data
    icon = Column(String)

    tier = Column(Integer)

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy="joined", cascade="all, delete")

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", lazy="joined", cascade="all, delete"
    )

    @orm.validates("tier")
    def validate_tier_number(self, key, value):
        if not 0 <= value <= 5:
            raise ValueError(f"Invalid ability tier {value}")
        return value