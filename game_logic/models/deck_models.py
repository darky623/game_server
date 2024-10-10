from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class AbsoluteDeck(Base):
    __tablename__ = 'absolute_decks'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref='absolute_decks', uselist=False)

    deck_id = Column(Integer, ForeignKey('deck.id'), nullable=True)
    deck = relationship('Deck', backref='')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'deck_id': self.deck_id
        }


class Deck(Base):
    __tablename__ = 'deck'

    id = Column(Integer, primary_key=True)
    title = Column(String(20), nullable=True)

    # character_id = Column(Integer, ForeignKey('Character.id'), nullable= False)

