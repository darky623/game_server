from sqlalchemy import select

from src.game_logic.models.battle_models import BattleModel
from src.game_logic.services.service import Service


class BattleService(Service):
    async def get_all_by_user(self, user_id):
        result = await self.session.execute(
            select(BattleModel).where(BattleModel.creator_id == user_id).order_by(BattleModel.created_at.desc())
        )

        return result.scalars().all()
