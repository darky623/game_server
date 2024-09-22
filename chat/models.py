from sqlalchemy import Column, Integer, VARCHAR, ForeignKey, DateTime, String, Table
from sqlalchemy.orm import relationship

from database import Base


users_chats = Table(
    'users_chats',
    Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, index=True)

    type = Column(String)
    users = relationship('User', secondary=users_chats, back_populates='chats', lazy='joined')
    messages = relationship('Message', back_populates='chat')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(VARCHAR(150), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', lazy='joined')
    timestamp = Column(DateTime)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship('Chat', back_populates='messages', lazy='joined')

    def serialize(self):
        return {
            'text': self.text,
            'timestamp': self.timestamp,
            'username': self.user.username,
            'user_id': self.user.id
        }
