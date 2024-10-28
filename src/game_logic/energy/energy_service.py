from datetime import datetime

from sqlalchemy import select

from config.config import dt_format
from src.game_logic.energy.models import Energy
from src.game_logic.energy.schema import EnergySchema, EnergyUpdateSchema


class EnergyService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_energy(self, user_id: int) -> EnergySchema | None:
        async with self.session_factory() as session:
            result = await session.execute(select(Energy).where(Energy.user_id == user_id))
            if result:
                return EnergySchema.from_orm(result.scalars().first())

    async def update_energy(self, user_id: int, amount: int) -> EnergyUpdateSchema | None:
        """
        Обновляет или создает энергию у пользователя

        Args:
            user_id (int): ID пользователя
            amount (int): Новое количество энергии

        Returns:
            EnergyUpdateSchema | None: Обновленная энергия, либо None если энергии не существует
        """
        async with self.session_factory() as session:
            energy = await session.execute(select(Energy).where(Energy.user_id == user_id)).scalars().first()
            if energy:
                # Прибавляем к энергии нужное количество единиц
                energy.amount += amount
                # Обновляем время ласт апдейта энергии
                current_time = datetime.now().strftime(dt_format)
                energy.last_updated = current_time
                await session.commit()
                return EnergyUpdateSchema.from_orm(energy)
            else:
                energy = Energy(user_id=user_id, amount=amount)
                await session.add(energy)
                await session.commit()
                return EnergyUpdateSchema.from_orm(energy)
