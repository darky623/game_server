from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    DateTime,
    func,
    Enum,
)
from sqlalchemy.orm import relationship

from auth.models import User
from src.chat.models import Chat
from config.database import Base


class Clan(Base):
    __tablename__ = "clans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(25), unique=True, nullable=False)
    short_name = Column(String(3), nullable=False)
    avatar = Column(String, nullable=True)
    rang = Column(Integer, default=1)
    is_public = Column(Boolean, default=True)
    is_ghost = Column(Boolean, default=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    chat_id = Column(Integer, ForeignKey("chats.id"))
    chat = relationship(Chat, backref="clan", uselist=False)

    # Subscribers
    subscribers_id = Column(Integer, ForeignKey("users.id"))
    subscribers = relationship(
        "SubscribeToClan",
        back_populates="clan",
        cascade="all, delete-orphan",
        viewonly=True,
    )

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "avatar": self.avatar,
            "chat_id": self.chat_id,
            "rang": self.rang,
        }


class SubscribeToClan(Base):
    """Класс для подписок на клан.
    Подписчики клана имеющие права на приглашение других людей отправляют заявку игроку
    формируется подписка со статусом False."""

    __tablename__ = "subscribe_to_clans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clan_id = Column(Integer, ForeignKey("clans.id"))
    role = Column(
        Enum(
            "Head",
            "Deputy",
            "Elder",
            "Officer",
            "Participant",
            name="role_enum",
            native_enum=False,
        ),
        default="Участник",
    )
    status = Column(Boolean, default=False)
    date_create = Column(DateTime, default=func.now())

    # Relationships
    user = relationship(User, backref="subscribe_to_clans", uselist=False)
    clan = relationship(Clan, back_populates="subscribers")


class RequestToClan(Base):
    """Класс для запросов на вступление в клан.
    Пользователь отправляется запрос на вступление в клан."""

    __tablename__ = "requests_to_clans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clan_id = Column(Integer, ForeignKey("clans.id"), nullable=False)
    status = Column(Boolean, default=False)
    date_create = Column(DateTime, default=func.now())

    # Relationships
    user = relationship(User, backref="requests_to_clans", uselist=False)
    clan = relationship(Clan, backref="requests_to_clans")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "clan_id": self.clan_id,
            "status": self.status,
            "date_create": self.date_create,
        }
