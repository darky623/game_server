from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from starlette import status

from src.game_logic.models.deck_models import Deck, DeckCharacter
from src.game_logic.schemas.character_schema import CharacterSchema
from src.game_logic.services.service import Service
from src.game_logic.models.models import Character

from src.game_logic.schemas.deck_schema import Deck as DeckSchema


class DeckService(Service):
    async def are_characters_owned_by_user(self,
                                           user_id: int,
                                           character_ids: List[int]
                                           ) -> bool:
        """Проверяет, принадлежат ли персонажи юзеру.
        Args:
            user_id (int): ID юзера
            character_ids (List[int]): ID персонажей
        Returns:
            bool: True, если персонажи принадлежат юзеру, иначе False"""
        character_query = select(Character).where(
            Character.id.in_(character_ids), Character.user_id == user_id
        )
        result = await self.session.execute(character_query)
        characters = result.scalars().all()
        return len(characters) == len(character_ids)

    async def create_deck(self, user_id: int,
                          character_ids: List[int]
                          ) -> DeckSchema:
        """Создает новую колоду для пользователя.
        Args:
            user_id (int): ID юзера
            character_ids (List[int]): ID персонажей
        Returns:
            DeckSchema: Новая колода
        """
        max_decks = 10  # Максимальное количество колод для любого игрока
        max_characters = 10  # Максимальное количество персонажей в колоде
        if len(character_ids) > max_characters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of characters in a deck is {max_characters}",
            )

        current_decks_count = len(await self.get_user_decks(user_id))
        if current_decks_count >= max_decks:
            raise HTTPException(400, detail="Deck limit reached")

        # Check if all character IDs belong to the user
        if self.are_characters_owned_by_user(user_id, character_ids) is False:
            raise HTTPException(400,
                                detail="Not all characters belong to the user")

        try:
            # Создаем новую колоду
            deck = Deck(
                user_id=user_id, is_active=False,
                deck_index=current_decks_count + 1
            )
            deck = await super().add(deck)

            for i, char_id in enumerate(character_ids):
                # Добавляем персонажей в колоду
                deck_char = DeckCharacter(
                    deck_id=deck.id, character_id=char_id, position=i + 1
                )
                await super().add(deck_char)

            return DeckSchema.from_orm(deck)
        except HTTPException as e:
            raise e
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}",
            )

    async def get_deck(self, deck_id: int) -> Optional[DeckSchema]:
        """Возвращает колоду по ID с полной информацией о героях.
        Args:
            deck_id (int): ID колоды
        Returns:
            DeckSchema: Колода с полной информацией о героях
        """
        try:
            query = (
                select(Deck)
                .options(
                    joinedload(Deck.characters)
                    .joinedload(DeckCharacter.character)
                )
                .where(Deck.id == deck_id)
            )
            result = await self.session.execute(query)
            deck = result.unique().scalars().first()

            if not deck:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deck not found"
                )

            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

    async def get_user_decks(self, user_id: int) -> List[DeckSchema]:
        """Возвращает все колоды пользователя. Без информации о героях
        Args:
            user_id (int): ID юзера
        Returns:
            List[DeckSchema]: Список колод

        """
        try:
            all_decks_user = await self.session.execute(
                select(Deck).where(Deck.user_id == user_id)
            )
            decks = list(all_decks_user.scalars().all())
            return [DeckSchema.from_orm(deck) for deck in decks]
        except HTTPException as e:
            raise e
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}",
            )

    async def get_user_deck_by_index(self,
                                     user_id: int,
                                     deck_index: int
                                     ) -> Optional[DeckSchema]:
        """Возвращает колоду пользователя по индексу.
        Args:
            user_id (int): ID юзера
            deck_index (int): Индекс колоды
        Returns:
            DeckSchema: Колода"""
        try:
            deck = await self.session.execute(
                select(Deck).where(
                    Deck.user_id == user_id,
                    Deck.deck_index == deck_index
                )
            )
            deck = deck.scalars().first()
            if not deck:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deck not found"
                )
            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}",
            )

    async def update_deck(self,
                          user_id: int,
                          deck_index: int,
                          character_ids: List[int],
                          is_active: bool = False
                          ) -> DeckSchema:
        """Обновляет колоду.  is_active=True сделает колоду активной, но только одну.
        Args:
            user_id (int): ID юзера
            deck_index (int): Индекс колоды
            character_ids (List[int]): ID персонажей
            is_active (bool): Активность колоды
            (по умолчанию False)
        Returns:
            DeckSchema: Обновленная колода
        """
        try:
            deck = await self.get_user_deck_by_index(user_id, deck_index)

            # Check if all character IDs belong to the user
            if self.are_characters_owned_by_user(user_id, character_ids) is False:
                raise HTTPException(400,
                                    detail="Not all characters belong to the user")

            if is_active:
                # Check if there are any active decks for this user
                decks_user = await self.get_user_decks(user_id)
                for not_current_deck in decks_user:
                    not_current_deck.is_active = False

                    await super().add(not_current_deck)

            # Update deck
            deck.character_ids = character_ids
            deck.is_active = is_active

            # Save changes
            await super().add(deck)

            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Database error: {e}")

    async def delete_deck_by_index(self,
                                   user_id: int,
                                   deck_index: int
                                   ) -> None:
        """Удаляет колоду.
        Args:
            user_id (int): ID юзера
            deck_index (int): ID колоды
        Returns:
            None
        """
        try:
            deck = await self.get_user_deck_by_index(user_id, deck_index)
            if deck:
                await self.session.delete(deck)
                await self.session.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deck not found"
                )
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Database error: {e}")

    async def get_active_deck(self, user_id: int) -> Optional[DeckSchema]:
        """Возвращает активную колоду пользователя с полной информацией о героях.
        Args:
            user_id (int): ID юзера
        Returns:
            DeckSchema: Активная колода с полной информацией о героях, если она есть, None иначе
        """
        try:
            query = (
                select(Deck)
                .options(
                    joinedload(Deck.characters)
                    .joinedload(DeckCharacter.character)
                )
                .where(Deck.user_id == user_id, Deck.is_active == True)
                .limit(1)
            )
            result = await self.session.execute(query)
            deck = result.unique().scalars().first()

            if not deck:
                return None

            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

    async def get_current_characters_in_deck(self,
                                             user_id: int,
                                             deck_index: int
                                             ) -> List[CharacterSchema]:
        """Возвращает персонажей в текущей колоде.
        Args:
            user_id (int): ID юзера
            deck_index (int): ID колоды
        Returns:
            List[CharacterSchema]: Список персонажей в текущей колоде
        """
        deck = await self.get_user_deck_by_index(user_id, deck_index)
        return [CharacterSchema.from_orm(character) for character in deck.characters]
