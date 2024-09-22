from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func, Enum
from sqlalchemy.orm import relationship

from auth.models import User
from chat.models import Chat
from database import Base


class Clan(Base):
    __tablename__ = 'clans'

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
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship(Chat, backref='clan', uselist=False)

    subscribers = relationship(
        "SubscribeToClan",
        back_populates="clan",
        cascade="all, delete-orphan"
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
    __tablename__ = 'subscribe_to_clans'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    clan_id = Column(Integer, ForeignKey('clans.id'))
    role = Column(Enum(
        'Глава', 'Заместитель', 'Старейшина', 'Офицер', 'Участник',
        name='role_enum',
        native_enum=False
    ), default='Участник')
    status = Column(Boolean, default=False)
    date_create = Column(DateTime, default=func.now())

    # Relationships
    user = relationship(User, backref='subscribe_to_clans', uselist=False)
    clan = relationship(Clan, backref='subscribe_to_clans')


class RequestToClan(Base):
    __tablename__ = 'requests_to_clans'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=False)
    status = Column(Boolean, default=False)
    date_create = Column(DateTime, default=func.now())

    # Relationships
    user = relationship(User, backref='requests_to_clans', uselist=False)
    clan = relationship(Clan, backref='requests_to_clans')
