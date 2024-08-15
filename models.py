from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
import config


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String)
    status = Column(String, default='active')
    create_date = Column(DateTime)
    auth_sessions = relationship("AuthSession", back_populates="user")
    characters = relationship("Character", back_populates="user")

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'status': self.status,
            'create_date': self.create_date.strftime(config.dt_format)
        }


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="auth_sessions")
    token = Column(String)
    status = Column(String, default="active")
    create_date = Column(DateTime)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'status': self.status,
            'create_date': self.create_date.strftime(config.dt_format)
        }


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="characters")
    name = Column(String)
    character_type = Column(String)
    archetype_id = Column(Integer, ForeignKey("character_archetypes.id"))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'archetype_id': self.archetype_id,
        }


class CharacterArchetype(Base):
    __tablename__ = "character_archetypes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)

    multiplier_params = Column(Integer, ForeignKey("multiplier_params.id"))
    summand_params = Column(Integer, ForeignKey("summand_params.id"))

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
