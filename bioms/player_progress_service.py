from fastapi import HTTPException, Depends
from sqlalchemy import select

from auth.models import User

from bioms.models import PlayerProgress
from bioms.schemas import PlayerProgressCreateSchema, PlayerProgressSchema


class PlayerProgressService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_player_progress(self, user_id: User) -> list[PlayerProgressSchema]:
        async with self.session_factory() as session:
            player = await session.execute(select(User).where(User.id == user_id))
            if player.exists():
                result = await session.execute(select(PlayerProgress).where(PlayerProgress.player.user_id == player))
                player_progress = result.scalars().all()
                return player_progress
            return HTTPException(404, detail='Player not found')

    async def create_player_progress(self, user_id: int) -> PlayerProgressSchema:
        async with self.session_factory() as session:
            player = await session.execute(select(User).where(User.id == user_id))
            if player.exists():
                player_progress = PlayerProgress(player_id=player.scalars().first().id)
                session.add(player_progress)
                await session.commit()
                await session.refresh(player_progress)
                return player_progress
            return HTTPException(404, 'Player not found')

    async def update_player_progress(self, user_id: int,
                                     update: PlayerProgressSchema) -> PlayerProgressSchema:
        async with self.session_factory() as session:
            result = await session.execute(select(PlayerProgress).where(PlayerProgress.player_id == user_id))
            player_progress = result.scalars().first()
            if not player_progress:
                raise HTTPException(404, "PlayerProgress not found")

            for key, value in update.dict().items():
                setattr(player_progress, key, value)

            await session.commit()
            await session.refresh(player_progress)
            return player_progress

    async def delete_player_progress(self, user_id: int, player_progress_id: int):
        async with self.session_factory() as session:
            result = await session.execute(select(PlayerProgress).where(PlayerProgress.id == player_progress_id))
            player_progress = result.scalars().first()
            if not player_progress:
                raise HTTPException(404, "PlayerProgress not found")

            await session.delete(player_progress)
            await session.commit()

