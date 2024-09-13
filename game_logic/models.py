from sqlalchemy import Column, Float, Integer, ForeignKey, String, Table, Enum, orm
from sqlalchemy.orm import relationship
from database import Base
import enum


character_items = Table(
    'character_items',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.id'), primary_key=True)
)


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    user = relationship("User", backref="characters", lazy='joined')
    name = Column(String)

    character_type_id = Column(Integer, ForeignKey('character_types.id'))
    character_type = relationship("CharacterType", backref='characters', lazy='joined')

    class_id = Column(Integer, ForeignKey("character_classes.id"))
    character_class = relationship("CharacterClass", backref='characters', lazy='joined')

    subclass_id = Column(Integer, ForeignKey('character_subclasses.id'))
    subclass = relationship('CharacterSubclass', lazy='joined')

    race_id = Column(Integer, ForeignKey('races.id'))
    race = relationship("Race", backref='characters', lazy='joined')

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams", backref='characters')

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams", backref='characters')

    fragments = Column(Integer)
    avatar = Column(String)
    stardom = Column(Integer)
    level = Column(Integer)

    base_params = None
    abilities = []

    def calculate_base_params(self):
        result = self.summand_params * (self.multiplier_params * self.level)
        result += self.archetype.summand_params + self.race.summand_params
        result *= self.archetype.multiplier_params * self.race.multiplier_params
        result += sum([item.summand_params for item in self.items])
        for item in self.items:
            result *= item.multiplier_params
            
        self.base_params = result
        return self.base_params

    def definite_abilities(self):
        ...

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


classes_abilities = Table(
    'classes_abilities',
    Base.metadata,
    Column('class_id', Integer, ForeignKey('character_classes.id'), primary_key=True),
    Column('ability_id', Integer, ForeignKey('abilities.id'), primary_key=True)
)


class CharacterClass(Base):
    __tablename__ = "character_classes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)
    icon = Column(String)

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship("MultiplierParams", lazy='selectin')

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy='selectin')

    subclasses = relationship('CharacterSubclass', back_populates='class')

    abilities = relationship('Ability', secondary=classes_abilities)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
        }


subclasses_abilities = Table(
    'subclasses_abilities',
    Base.metadata,
    Column('subclass_id', Integer, ForeignKey('character_subclasses.id'), primary_key=True),
    Column('ability_id', Integer, ForeignKey('abilities.id'), primary_key=True)
)


class CharacterSubclass(Base):
    __tablename__ = "character_subclasses"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)
    icon = Column(String)

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship("MultiplierParams", lazy='joined')

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy='joined')

    character_class_id = Column(Integer, ForeignKey('character_classes.id'))
    character_class = relationship('CharacterClass', back_populates='subclasses', lazy='joined')

    abilities = relationship('Ability', secondary=subclasses_abilities)


class MultiplierParams(Base):
    __tablename__ = "multiplier_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=1)
    vitality = Column(Float, default=1)
    speed = Column(Float, default=1)
    resistance = Column(Float, default=1)
    critical_hit_chance = Column(Float, default=1)
    evasion = Column(Float, default=1)
    true_damage = Column(Float, default=1)
    spirit = Column(Float, default=1)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MultiplierParams(
                damage=self.damage * other,
                vitality=self.vitality * other,
                speed=self.speed * other,
                resistance=self.physical_resistance * other,
                critical_hit_chance=self.critical_hit_chance * other,
                evasion=self.evasion * other,
                true_damage=self.true_damage * other,
                spirit=self.spirit * other
            )
        elif isinstance(other, MultiplierParams):
            return MultiplierParams(
                damage=self.damage * other.damage,
                vitality=self.vitality * other.vitality,
                speed=self.speed * other.speed,
                resistance=self.physical_resistance * other.resistance,
                critical_hit_chance=self.critical_hit_chance * other.critical_hit_chance,
                evasion=self.evasion * other.evasion,
                true_damage=self.true_damage * other.true_damage,
                spirit=self.spirit * other.spirit
            )
        elif isinstance(other, SummandParams):
            return SummandParams(
                damage=self.damage * other.damage,
                vitality=self.vitality * other.vitality,
                speed=self.speed * other.speed,
                resistance=self.physical_resistance * other.resistance,
                critical_hit_chance=self.critical_hit_chance * other.critical_hit_chance,
                evasion=self.evasion * other.evasion,
                true_damage=self.true_damage * other.true_damage,
                spirit=self.spirit * other.spirit
            )
        return NotImplemented


class SummandParams(Base):
    __tablename__ = "summand_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=0)
    vitality = Column(Float, default=0)
    speed = Column(Float, default=0)
    resistance = Column(Float, default=0)
    critical_hit_chance = Column(Float, default=0)
    evasion = Column(Float, default=0)
    true_damage = Column(Float, default=0)
    spirit = Column(Float, default=0)

    def __add__(self, other):
        if isinstance(other, SummandParams):
            return SummandParams(
                damage=self.damage + other.damage,
                vitality=self.vitality + other.vitality,
                speed=self.speed + other.speed,
                resistance=self.physical_resistance + other.resistance,
                critical_hit_chance=self.critical_hit_chance + other.critical_hit_chance,
                evasion=self.evasion + other.evasion,
                true_damage=self.true_damage + other.true_damage,
                spirit=self.spirit + other.spirit
            )
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return SummandParams(
                damage=self.damage * other,
                vitality=self.vitality * other,
                speed=self.speed * other,
                resistance=self.physical_resistance * other,
                critical_hit_chance=self.critical_hit_chance * other,
                evasion=self.evasion * other,
                true_damage=self.true_damage * other,
                spirit=self.spirit * other
            )
        return NotImplemented


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    level = Column(Integer)
    icon = Column(String)

    tier = relationship(Integer)

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")

    @orm.validates('tier')
    def validate_tier_number(self, key, value):
        if not 0 <= value <= 5:
            raise ValueError(f'Invalid ability tier {value}')
        return value


races_abilities = Table(
    'races_abilities',
    Base.metadata,
    Column('race_id', Integer, ForeignKey('races.id'), primary_key=True),
    Column('ability_id', Integer, ForeignKey('abilities.id'), primary_key=True)
)


class Race(Base):
    __tablename__ = 'races'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'))
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'))
    multiplier_params = relationship("MultiplierParams")

    abilities = relationship('Ability', secondary=races_abilities, lazy='joined')


class TriggerCondition(enum.Enum):
    ON_START = 'on_start'
    ON_MOTION_START = 'on_motion_end'
    ON_COMMON_ATTACK = 'on_common_attack'
    ON_ULTIMATE_ATTACK = 'on_ultimate_attack'
    PASSIVE = 'passive'
    ON_BUFF = 'on_buff'
    ON_DEBUFF = 'on_debuff'
    ON_DEATH = 'on_death'
    ON_TEAMMATE_ATTACK = 'on_teammate_attack'
    ON_REVIVE = 'on_revive'
    ON_SUMMONED = 'on_summoned'


class Ability(Base):
    __tablename__ = 'abilities'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    icon = Column(String)

    tier = Column(Integer, nullable=False, default=0)

    ability_type_id = Column(Integer, ForeignKey('ability_types.id'))
    ability_type = relationship('AbilityType')

    summand_params_id = Column(Integer, ForeignKey('summand_params.id'), nullable=True)
    summand_params = relationship("SummandParams")

    multiplier_params_id = Column(Integer, ForeignKey('multiplier_params.id'), nullable=True)
    multiplier_params = relationship("MultiplierParams")

    chance = Column(Float, default=1)
    summoned_character_id = Column(Integer, ForeignKey('characters.id'), nullable=True)
    summoned_character = relationship('Character', lazy='joined')
    summoned_quantity = Column(Integer, default=0)

    trigger_condition = Column(Enum(TriggerCondition), nullable=False)

    damage = Column(Integer, default=0)
    healing = Column(Integer, default=0)

    @orm.validates('tier')
    def validate_tier_number(self, key, value):
        if not 0 <= value <= 5:
            raise ValueError(f'Invalid ability tier {value}')
        return value


class AbilityType(Base):
    __tablename__ = 'ability_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
