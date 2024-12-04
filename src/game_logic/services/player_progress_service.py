from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.game_logic.models.biome_models import PlayerProgress
from src.game_logic.schemas.player_progress_schema import PlayerProgressSchema
from src.game_logic.services.service import Service


class PlayerProgressService(Service):

    async def get_player_progress(self, user_id: int) -> PlayerProgressSchema:
        try:
            result = await self.session.execute(
                select(PlayerProgress).where(PlayerProgress.player_id == user_id)
            )
            player_progress = result.scalars().first()
            if player_progress is None:
                raise HTTPException(404, "PlayerProgress not found")

            return PlayerProgressSchema.from_orm(player_progress)

        except SQLAlchemyError as e:
            raise HTTPException(500, "Error getting player progress") from e

    async def create_player_progress(self, user_id: int) -> PlayerProgressSchema:
        try:
            result = await self.session.execute(
                select(PlayerProgress).where(PlayerProgress.player_id == user_id)
            )

            current_player_progress = result.scalars().first()
            if current_player_progress is None:
                new_player_progress = PlayerProgress(player_id=user_id)

                await super().add(new_player_progress)
                return PlayerProgressSchema.from_orm(new_player_progress)

            raise HTTPException(409, "PlayerProgress already exists")
        except SQLAlchemyError as e:
            raise HTTPException(500, "Error creating player progress") from e

    async def update_player_progress(self, update: PlayerProgressSchema,
                                     user_id: int) -> PlayerProgressSchema:
        try:
            if update.player_id != user_id:
                raise HTTPException(400, "PlayerProgress does not belong to user")
            result = await self.session.execute(
                select(PlayerProgress).where(PlayerProgress.id == update.player_id)
            )
            player_progress = result.scalars().first()
            if player_progress is None:
                raise HTTPException(404, "PlayerProgress not found")

            for key, value in update.dict().items():
                if hasattr(player_progress, key):
                    setattr(player_progress, key, value)

            await super().add(player_progress)

            return PlayerProgressSchema.from_orm(player_progress)
        except SQLAlchemyError as e:
            raise HTTPException(500, "Error updating player progress") from e

    async def delete_player_progress(self, user_id: int):

        try:
            result = await self.session.execute(
                select(PlayerProgress).where(PlayerProgress.player_id == user_id)
            )
            player_progress = result.scalars().first()
            if player_progress is None:
                raise HTTPException(404, "PlayerProgress not found")

            await self.session.delete(player_progress)
            await self.session.commit()
            await self.session.refresh(player_progress)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(500, "Error deleting player progress") from e
