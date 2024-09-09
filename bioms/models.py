from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from database import Base

biome_boss_abilities = Table(
    "biome_boss_abilities",
    Base.metadata,
    Column("biome_id", Integer, ForeignKey("biomes.id")),
    Column("ability_id", Integer, ForeignKey("abilities.id")),
)

boss_abilities = Table(
    "boss_abilities",
    Base.metadata,
    Column("boss_id", Integer, ForeignKey("bosses.id")),
    Column("ability_id", Integer, ForeignKey("abilities.id")),
)


class Biome(Base):
    __tablename__ = "biomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), nullable=False)
    description = Column(Text)
    difficulty_lvl = Column(Integer, default=1)

    reward_id = Column(Integer, ForeignKey("rewards.id"))
    reward = relationship("Reward", backref="biomes")

    boss_abilities = relationship(
        "Ability", secondary=biome_boss_abilities, backref="biomes"
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

    battles = Column(Integer,default=0)
    victories = Column(Integer, default=0)
    defeats = Column(Integer, default=0)
    current_difficulty_level = Column(Integer, default=1)


class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    reward_type = Column(String(25))
    quantity = Column(Integer)


class Ability(Base):
    __tablename__ = "abilities"
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    damage = Column(Integer, nullable=False)
    description = Column(Text)


class Boss(Base):
    __tablename__ = "bosses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    abilities = relationship(
        "Ability", secondary=biome_boss_abilities, back_populates="bosses"
    )
    biome_levels = relationship("BiomeLevel", back_populates="boss")
