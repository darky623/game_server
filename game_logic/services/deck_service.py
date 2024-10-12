from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import insert, select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.sync import update
from starlette import status

from game_logic.models.deck_models import Deck, DeckCharacter
from game_logic.services.service import Service
from game_logic.models.models import Character

from game_logic.schemas.deck_schema import Deck as DeckSchema


class DeckService(Service):
    async def are_characters_owned_by_user(
        self, user_id: int, character_ids: List[int]
    ) -> bool:
        """"Проверяет, принадлежат ли персонажи юзеру.
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

    async def create_deck(self, user_id: int, character_ids: List[int]) -> DeckSchema:
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
            raise HTTPException(400, detail="Not all characters belong to the user")

        try:
            # Создаем новую колоду
            deck = Deck(
                user_id=user_id, is_active=False, deck_index=current_decks_count + 1
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
        """Возвращает колоду по ID.
        Args:
            deck_id (int): ID колоды
        Returns:
            DeckSchema: Колода
        """
        try:
            deck = await self.session.execute(select(Deck).where(Deck.id == deck_id))
            deck = deck.scalars().first()
            if not deck:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
                )
            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}",
            )

    async def get_user_decks(self, user_id: int) -> List[DeckSchema]:
        """Возвращает все колоды пользователя.
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

    async def get_user_deck_by_index(
        self, user_id: int, deck_index: int
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
                    Deck.user_id == user_id, Deck.deck_index == deck_index
                )
            )
            deck = deck.scalars().first()
            if not deck:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
                )
            return DeckSchema.from_orm(deck)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}",
            )

    async def update_deck(
        self, user_id: int, deck_index: int, character_ids: List[int], is_active: bool = False
    ) -> DeckSchema:
        """Обновляет колоду.  is_active=True сделает колоду активной, но только одну."""
        try:
            deck = await self.get_user_deck_by_index(user_id, deck_index)

            # Check if all character IDs belong to the user
            if self.are_characters_owned_by_user(user_id, character_ids) is False:
                raise HTTPException(400, detail="Not all characters belong to the user")

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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

    async def delete_deck(self, deck_id: int) -> None:
        """Удаляет колоду."""
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    delete(DeckCharacter).where(DeckCharacter.deck_id == deck_id)
                )
                await session.execute(delete(Deck).where(Deck.id == deck_id))
                await session.commit()

    async def get_active_deck(self, user_id: int) -> Optional[Deck]:
        """Возвращает активную колоду пользователя."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Deck)
                .where(Deck.user_id == user_id, Deck.is_active == True)
                .limit(1)
            )
            return result.scalars().first()

    async def get_deck_by_index(self, user_id: int, deck_index: int) -> Optional[Deck]:
        """Возвращает колоду по user_id и deck_index."""
        async with self.session_factory() as session:
            stmt = (
                select(Deck)
                .join(UserDeck)
                .where(UserDeck.user_id == user_id, UserDeck.deck_index == deck_index)
            )
            result = await session.execute(stmt)
            user_deck = result.scalars().first()
            return user_deck.deck if user_deck else None

    async def get_user_decks(self, user_id: int) -> List[Tuple[Deck, int]]:
        """Возвращает все колоды пользователя с deck_index."""
        async with self.session_factory() as session:
            stmt = (
                select(Deck, UserDeck.deck_index)
                .join(UserDeck)
                .where(UserDeck.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.all()
