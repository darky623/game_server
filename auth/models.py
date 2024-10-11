from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import config as settings
from database import Base
from chat.models import users_chats
from game_logic.models import Character


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String)
    status = Column(String, default='active')
    create_date = Column(DateTime)
    last_login = Column(DateTime)
    auth_sessions = relationship("AuthSession", back_populates="user", lazy='joined')
    characters = relationship("Character", back_populates="user")
    chats = relationship("Chat", secondary=users_chats, back_populates='users', lazy='joined')
    player_progress = relationship("PlayerProgress", back_populates="player", lazy='selectin')
    decks = relationship("Deck", back_populates="owner")

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'status': self.status,
            'create_date': self.create_date.strftime(settings.dt_format)
        }


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="auth_sessions", lazy='joined')
    token = Column(String)
    status = Column(String, default="active")
    create_date = Column(DateTime)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'status': self.status,
            'create_date': self.create_date.strftime(settings.dt_format)
        }