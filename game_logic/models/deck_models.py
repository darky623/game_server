from sqlalchemy import Column, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Deck(Base):
    """ Один пресет колоды.
    Класс для колод пользователей, пользователь может иметь несколько колод."""
    __tablename__ = "decks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=False)
    deck_index = Column(Integer, unique=True)  # Индекс пресета колоды для пользователя

    owner = relationship("User", back_populates="decks")
    characters = relationship("DeckCharacter", back_populates="deck")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "deck_index": self.deck_index,
        }


class DeckCharacter(Base):
    """ Непосредственно сама карточка в колоде.
    Класс для связи конкретной колоды игрока и персонажей, которые будут в ней присутствовать."""

    __tablename__ = "deck_characters"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.deck_index"))
    character_id = Column(Integer, ForeignKey("characters.id"))
    position = Column(Integer)  # Позиция в колоде (0-9)

    deck = relationship("Deck", back_populates="characters")
    character = relationship("Character")

    def serialize(self):
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "character_id": self.character_id,
            "position": self.position,
        }
