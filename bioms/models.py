from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from database import Base

boss_abilities = Table(
    "boss_abilities",
    Base.metadata,
    Column("boss_id", Integer, ForeignKey("bosses.id"), primary_key=True),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
)


class Biome(Base):
    __tablename__ = "biomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False, unique=True)
    description = Column(Text)
    difficulty_lvl = Column(Integer, default=1)

    reward_id = Column(Integer, ForeignKey("rewards.id"))
    reward = relationship("Reward", backref="biomes")

    boss_abilities = relationship(
        "Ability", secondary=boss_abilities, backref="biomes"
    )

    levels = relationship("BiomeLevel", back_populates="biomes")
    player_progress = relationship("PlayerProgress", back_populates="biomes")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "difficulty_lvl": self.difficulty_lvl,
            "reward": self.reward.serialize(),
        }


class BiomeLevel(Base):
    __tablename__ = "biome_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number_of_lvl = Column(Integer, default=1)
    biome_id = Column(Integer, ForeignKey("biomes.id"))
    biome = relationship("Biome", back_populates="biome_levels")

    boss_id = Column(Integer, ForeignKey("bosses.id"))
    boss = relationship("Boss", backref="biome_level")

    reward_id = Column(Integer, ForeignKey("rewards.id"))
    reward = relationship("Reward", backref="biome_level")

    def serialize(self):
        return {
            "id": self.id,
            "boss": self.boss.serialize(),
            "reward": self.reward.serialize(),
            "biome": self.biome.serialize(),
        }


class PlayerProgress(Base):
    __tablename__ = "player_progress"
    id = Column(Integer, primary_key=True, index=True)

    biome_id = Column(Integer, ForeignKey("biomes.id"))
    biome = relationship("Biome", back_populates="player_progress")

    biome_level_id = Column(Integer, ForeignKey("biome_levels.id"))
    biome_level = relationship("BiomeLevel", back_populates="player_progress")

    battles = Column(Integer, default=0)
    victories = Column(Integer, default=0)
    defeats = Column(Integer, default=0)
    current_difficulty_level = Column(Integer, default=1)

    def serialize(self):
        return {
            "id": self.id,
            "biome": self.biome.serialize(),
            "biome_level": self.biome_level.serialize(),
        }


class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    reward_type = Column(String(25))
    quantity = Column(Integer)

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "reward_type": self.reward_type,
            "quantity": self.quantity,
        }


class Boss(Base):
    __tablename__ = "bosses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    ability = relationship("Ability", secondary=boss_abilities, back_populates="bosses")
    biome_levels = relationship("BiomeLevel", back_populates="bosses")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "abilities": [ability.serialize() for ability in self.abilities],
        }