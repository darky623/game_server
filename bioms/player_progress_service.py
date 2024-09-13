from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from auth.models import User

from bioms.models import PlayerProgress
from bioms.schemas import PlayerProgressSchema


class PlayerProgressService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_player_progress(self, user_id: User) -> PlayerProgressSchema:
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(PlayerProgress).where(PlayerProgress.player_id == user_id)
                )
                player_progress = result.scalars().all()
                if not player_progress:
                    raise HTTPException(404, "PlayerProgress not found")
                return player_progress[0]
            except SQLAlchemyError as e:
                raise RuntimeError("Error getting player progress") from e

    async def create_player_progress(self, user_id: int) -> PlayerProgressSchema:
        async with self.session_factory() as session:
            try:
                current_player_progress = await session.execute(select(PlayerProgress).where(
                    PlayerProgress.player_id == user_id)
                )
                if current_player_progress.scalars().first() is None:
                    new_player_progress = PlayerProgress(player_id=user_id)

                    session.add(new_player_progress)
                    await session.commit()
                    await session.refresh(new_player_progress)
                    return new_player_progress
                raise HTTPException(409, "PlayerProgress already exists")
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(500, "Error creating player progress") from e

    async def update_player_progress(
        self, update: PlayerProgressSchema
    ) -> PlayerProgressSchema:
        async with self.session_factory() as session:
            try:
                result = await session.execute(
                    select(PlayerProgress).where(PlayerProgress.id == update.id)
                )
                player_progress = result.scalars().first()
                if not player_progress:
                    raise HTTPException(404, "PlayerProgress not found")

                for key, value in update.dict().items():
                    if hasattr(player_progress, key):
                        setattr(player_progress, key, value)

                await session.commit()
                await session.refresh(player_progress)
                return player_progress
            except SQLAlchemyError as e:
                await session.rollback()
                raise HTTPException(500, "Error updating player progress") from e

    async def delete_player_progress(self, user_id: int):
        async with self.session_factory() as session:
            # try:
            result = await session.execute(
                select(PlayerProgress).where(PlayerProgress.player_id == user_id)
            )
            player_progress = result.scalars().first()
            if not player_progress:
                raise HTTPException(404, "PlayerProgress not found")

            await session.delete(player_progress)
            await session.commit()
            await session.refresh(player_progress)
            # except SQLAlchemyError as e:
            #     await session.rollback()
            #     raise HTTPException(500, "Error deleting player progress") from e
