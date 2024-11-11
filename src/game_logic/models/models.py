from email.policy import default

from sqlalchemy import Column, Float, Integer, ForeignKey, String, Table, Enum, orm, ColumnElement
from sqlalchemy.orm import relationship
from config.database import Base
import enum


character_items = Table(
    "character_items",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id"), primary_key=True),
)

character_runes = Table(
    "character_runes",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("rune_id", Integer, ForeignKey("runes.id"), primary_key=True),
)


class CharacterType(enum.Enum):
    MAIN = "main"
    SECONDARY = "secondary"
    COLLECTIBLE = "collectible"
    BOSS = "boss"


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    user = relationship("User", back_populates="characters", lazy="joined")
    name = Column(String)

    character_type = Column(Enum(CharacterType), nullable=False)

    class_id = Column(Integer, ForeignKey("character_classes.id"))
    character_class = relationship(
        "CharacterClass", backref="characters", lazy="joined"
    )

    subclass_id = Column(Integer, ForeignKey("character_subclasses.id"))
    subclass = relationship("CharacterSubclass", lazy="joined")

    race_id = Column(Integer, ForeignKey("races.id"))
    race = relationship("Race", backref="characters", lazy="joined")

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy="joined", cascade="all, delete")

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", lazy="joined", cascade="all, delete"
    )

    items = relationship("Item", secondary=character_items, lazy="joined")

    runes = relationship("Rune", secondary=character_runes, lazy="joined")

    fragments = Column(Integer, default=0)
    avatar = Column(String)
    stardom = Column(Integer)
    level = Column(Integer)
    power = Column(Integer, default=0)
    base_params = None
    abilities = []

    def calculate_power(self):
        # Высчитывает мощность героя по формуле stardom*1000 + level*1,01 + ability_power(зависит от прокачки)
        tier_power_mapping = {
            1: 10,
            2: 250,
            3: 500,
            4: 750,
            5: 1000,
        }

        ability_power = 0
        active_abilities = character_controller.get_active_abilities()
        for tier, ability_controller in active_abilities.items():
            ability_power += tier_power_mapping.get(tier, 0)

        self.power = self.stardom * 1000 + self.level * 1.01 + ability_power
        return self.power

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "class_id": self.class_id,
        }


classes_abilities = Table(
    "classes_abilities",
    Base.metadata,
    Column("class_id", Integer, ForeignKey("character_classes.id"), primary_key=True),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
)


class CharacterClass(Base):
    __tablename__ = "character_classes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)
    icon = Column(String)

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", lazy="joined", cascade="all, delete"
    )

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy="joined", cascade="all, delete")

    subclasses = relationship(
        "CharacterSubclass",
        back_populates="character_class",
        lazy="joined",
        cascade="all, delete",
    )

    abilities = relationship("Ability", secondary=classes_abilities, lazy="joined")

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
        }


subclasses_abilities = Table(
    "subclasses_abilities",
    Base.metadata,
    Column(
        "subclass_id", Integer, ForeignKey("character_subclasses.id"), primary_key=True
    ),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
)


class CharacterSubclass(Base):
    __tablename__ = "character_subclasses"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)
    icon = Column(String)

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", lazy="joined", cascade="all, delete"
    )

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", lazy="joined", cascade="all, delete")

    character_class_id = Column(Integer, ForeignKey("character_classes.id"))
    character_class = relationship("CharacterClass", back_populates="subclasses")

    abilities = relationship("Ability", secondary=subclasses_abilities, lazy="joined")


class MultiplierParams(Base):
    __tablename__ = "multiplier_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=1)
    vitality = Column(Float, default=1)
    speed = Column(Float, default=1)
    resistance = Column(Float, default=1)
    evasion = Column(Float, default=1)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MultiplierParams(
                damage=self.damage * other,
                vitality=self.vitality * other,
                speed=self.speed * other,
                resistance=self.resistance * other,
                evasion=self.evasion * other,
            )
        elif isinstance(other, MultiplierParams):
            return MultiplierParams(
                damage=self.damage * other.damage,
                vitality=self.vitality * other.vitality,
                speed=self.speed * other.speed,
                resistance=self.resistance * other.resistance,
                evasion=self.evasion * other.evasion,
            )
        elif isinstance(other, SummandParams):
            return SummandParams(
                damage=self.damage * other.damage,
                vitality=self.vitality * other.vitality,
                speed=self.speed * other.speed,
                resistance=self.resistance * other.resistance,
                evasion=self.evasion * other.evasion,
            )
        return NotImplemented


class SummandParams(Base):
    __tablename__ = "summand_params"

    id = Column(Integer, primary_key=True, index=True)

    damage = Column(Float, default=0)
    vitality = Column(Float, default=0)
    speed = Column(Float, default=0)
    resistance = Column(Float, default=0)
    evasion = Column(Float, default=0)

    def __add__(self, other):
        if isinstance(other, SummandParams):
            return SummandParams(
                damage=self.damage + other.damage,
                vitality=self.vitality + other.vitality,
                speed=self.speed + other.speed,
                resistance=self.resistance + other.resistance,
                evasion=self.evasion + other.evasion,
            )
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return SummandParams(
                damage=self.damage * other,
                vitality=self.vitality * other,
                speed=self.speed * other,
                resistance=self.resistance * other,
                evasion=self.evasion * other,
            )
        if isinstance(other, MultiplierParams):
            return other * self
        return NotImplemented


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    level = Column(Integer)
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


races_abilities = Table(
    "races_abilities",
    Base.metadata,
    Column("race_id", Integer, ForeignKey("races.id"), primary_key=True),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
)


class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship(
        "SummandParams", lazy="joined", cascade="all, delete", single_parent=True
    )

    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", lazy="joined", cascade="all, delete", single_parent=True
    )

    abilities = relationship("Ability", secondary=races_abilities, lazy="joined")


class TriggerCondition(enum.Enum):
    ON_START = "on_start"
    ON_MOTION_START = "on_motion_end"
    ON_COMMON_ATTACK = "on_common_attack"
    ON_ULTIMATE_ATTACK = "on_ultimate_attack"
    PASSIVE = "passive"
    ON_BUFF = "on_buff"
    ON_DEBUFF = "on_debuff"
    ON_DEATH = "on_death"
    ON_TEAMMATE_ATTACK = "on_teammate_attack"
    ON_REVIVE = "on_revive"
    ON_SUMMONED = "on_summoned"


class Ability(Base):
    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    icon = Column(String)
    visual = Column(String, default='noetic')

    tier = Column(Integer, nullable=False, default=0)

    ability_type_id = Column(Integer, ForeignKey("ability_types.id"))

    ability_type = relationship("AbilityType", lazy="joined", cascade="all, delete")

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"), nullable=True)
    summand_params = relationship("SummandParams", cascade="all, delete", lazy="joined")

    multiplier_params_id = Column(
        Integer, ForeignKey("multiplier_params.id"), nullable=True
    )
    multiplier_params = relationship(
        "MultiplierParams", cascade="all, delete", lazy="joined"
    )

    chance = Column(Float, default=1)
    summoned_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    summoned_character = relationship("Character")
    summoned_quantity = Column(Integer, default=0)

    target = Column(String, default="self")
    effect = Column(String)
    trigger_condition = Column(Enum(TriggerCondition), nullable=False)

    damage = Column(Integer, default=0)
    healing = Column(Integer, default=0)

    @orm.validates("tier")
    def validate_tier_number(self, key, value):
        if not 0 <= value <= 5:
            raise ValueError(f"Invalid ability tier {value}")
        return value


class AbilityType(Base):
    __tablename__ = "ability_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


runes_abilities = Table(
    "runes_abilities",
    Base.metadata,
    Column("rune_id", Integer, ForeignKey("runes.id"), primary_key=True),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
)


class Rune(Base):
    __tablename__ = "runes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    level = Column(Integer)

    summand_params_id = Column(Integer, ForeignKey("summand_params.id"))
    summand_params = relationship("SummandParams", cascade="all, delete", lazy="joined")
    multiplier_params_id = Column(Integer, ForeignKey("multiplier_params.id"))
    multiplier_params = relationship(
        "MultiplierParams", cascade="all, delete", lazy="joined"
    )

    abilities = relationship("Ability", secondary=runes_abilities, lazy="joined")
