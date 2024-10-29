from datetime import datetime

from sqlalchemy import select
from starlette.responses import JSONResponse

from config import game_settings
from config.config import dt_format
from src.game_logic.energy.models import Energy
from src.game_logic.energy.schema import EnergySchema


class EnergyService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_energy(self, user_id: int) -> EnergySchema:
        """
        Возвращает энергию пользователя, если ее нет - создаёт энергию
        Args:
            user_id (int): ID пользователя
        Returns:
            EnergySchema: Энергия пользователя
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Energy).where(Energy.user_id == user_id))
            if not result:
                # Create energy if it doesn't exist
                energy = Energy(user_id=user_id, amount=100, last_updated=datetime.now().strftime(dt_format))
                await session.add(energy)
                await session.commit()
                return EnergySchema.from_orm(energy)
            return EnergySchema.from_orm(result.scalars().first())

    async def update_energy(self, user_id: int, amount: int) -> EnergySchema | JSONResponse:
        """
        Обновляет или создает энергию у пользователя
        Args:
            user_id (int): ID пользователя
            amount (int): Новое количество энергии(может быть отрицательным)
        Returns:
            EnergyUpdateSchema | None: Обновленная энергия, либо None если энергии не существует
        """
        async with self.session_factory() as session:
            try:

                energy = await session.execute(select(Energy).where(Energy.user_id == user_id)).scalars().first()
                if energy:
                    # Прибавляем к энергии нужное количество единиц
                    energy.amount += amount
                    if energy.amount < game_settings.energy['energy_min']:

                        # Если энергии меньше минимального значения, то возвращаем ошибку
                        return JSONResponse(status_code=400, content={"message": "Недостаточно энергии"})
                    if energy.amount > game_settings.energy['energy_max']:
                        energy.amount = game_settings.energy['energy_max']
                    # Обновляем время ласт апдейта энергии
                    current_time = datetime.now().strftime(dt_format)
                    energy.last_updated = current_time
                    await session.commit()
                    return EnergySchema.from_orm(energy)
                else:
                    energy = Energy(user_id=user_id, amount=amount)
                    await session.add(energy)
                    await session.commit()
                    return EnergySchema.from_orm(energy)

            except Exception as e:
                return JSONResponse(status_code=500, content={"message": str(e)})
