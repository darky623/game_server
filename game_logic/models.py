from sqlalchemy import Column, Float, Integer, ForeignKey, String, Table
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="characters")
    name = Column(String)

    character_type_id = Column(Integer, ForeignKey('character_types.id'))
    character_type = relationship("CharacterType")

    archetype_id = Column(Integer, ForeignKey("character_archetypes.id"))
    archetype = relationship("CharacterArchetype")

    race_id = Column(Integer, ForeignKey('races.id'))
    race = relationship("Race")

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")

    items = relationship('Item', back_populates='character')

    avatar = Column(String)
    stardom = Column(Integer)
    level = Column(Integer)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'archetype_id': self.archetype_id,
        }


class CharacterType(Base):
    __tablename__ = 'character_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class CharacterArchetype(Base):
    __tablename__ = "character_archetypes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship("MultiplierParams")

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams")

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
        }


class MultiplierParams(Base):
    __tablename__ = "multiplier_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=1)
    vitality = Column(Float, default=1)
    strength = Column(Float, default=1)
    agility = Column(Float, default=1)
    intelligence = Column(Float, default=1)
    speed = Column(Float, default=1)
    physical_resistance = Column(Float, default=1)
    magical_resistance = Column(Float, default=1)
    critical_hit_chance = Column(Float, default=1)
    evasion = Column(Float, default=1)
    true_damage = Column(Float, default=1)
    accuracy = Column(Float, default=1)
    spirit = Column(Float, default=1)


class SummandParams(Base):
    __tablename__ = "summand_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=0)
    vitality = Column(Float, default=0)
    strength = Column(Float, default=0)
    agility = Column(Float, default=0)
    intelligence = Column(Float, default=0)
    speed = Column(Float, default=0)
    physical_resistance = Column(Float, default=0)
    magical_resistance = Column(Float, default=0)
    critical_hit_chance = Column(Float, default=0)
    evasion = Column(Float, default=0)
    true_damage = Column(Float, default=0)
    accuracy = Column(Float, default=0)
    spirit = Column(Float, default=0)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    level = Column(Integer)
    icon = Column(String)

    tier_id = Column(Integer, ForeignKey('item_tiers.id'))
    tier = relationship('ItemTier')

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")


character_items = Table(
    'character_items',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.id'), primary_key=True)
)


class ItemTier(Base):
    __tablename__ = 'item_tiers'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)


class Race(Base):
    __tablename__ = 'races'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")


class Ability(Base):
    __tablename__ = 'abilities'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    icon = Column(String)

    ability_tier_id = Column(Integer, ForeignKey('skill_tiers.id'))
    ability_tier = relationship('AbilityTier')

    ability_type_id = Column(Integer, ForeignKey('ability_types.id'))
    ability_type = relationship('AbilityType')

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")

    chance = Column(Float)
    summoned_character_id = Column(Integer, ForeignKey('character.id'), nullable=True)
    summoned_quantity = Column(Integer, default=0)

    damage = Column(Integer, default=0)
    healing = Column(Integer, default=0)


class AbilityType(Base):
    __tablename__ = 'ability_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class AbilityTier(Base):
    __tablename__ = 'ability_tiers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)



