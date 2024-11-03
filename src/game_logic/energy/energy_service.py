from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from config import game_settings
from config.config import dt_format
from config.game_settings import energy_per_time, time_add_one_energy
from src.game_logic.energy.models import Energy
from src.game_logic.energy.schema import EnergySchema
import logging

logger = logging.getLogger(__name__)


async def handle_exceptions(action):
    try:
        return await action()
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


def error_handler(func):
    async def wrapper(*args, **kwargs):
        result = await handle_exceptions(lambda: func(*args, **kwargs))
        if isinstance(result, dict) and result["status_code"] == 500:
            raise HTTPException(status_code=500, detail=result["message"])
        return result

    return wrapper


class EnergyService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.max_energy = game_settings.energy["energy_max"]

    @staticmethod
    async def _create_energy(user_id: int, session):
        """
        Создает энергию пользователя
        Args:
            user_id (int): ID пользователя
        """
        try:
            energy = Energy(user_id=user_id)
            session.add(energy)
            await session.commit()
            return EnergySchema.from_orm(energy)
        except Exception as e:
            logger.error(f"Error creating energy: {e}")
            return None

    @staticmethod
    async def _get_energy(user_id: int, session):
        try:
            result = await session.execute(
                select(Energy).where(Energy.user_id == user_id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting energy: {e}")
            return None

    async def energy_is_full(self, user_id: int) -> bool:
        """
        Проверяет, заполнена ли энергия пользователя
        Args:
            user_id (int): ID пользователя
        Returns:
            bool: True, если энергия полна, иначе False
        """
        async with self.session_factory() as session:
            energy = await self._get_energy(user_id, session)
            return (
                    energy is not None and energy.amount >= self.max_energy
            )

    async def get_energy(self, user_id: int) -> EnergySchema | JSONResponse:
        """
        Возвращает энергию пользователя, если ее нет - создаёт энергию
        Args:
            user_id (int): ID пользователя
        Returns:
            EnergySchema: Энергия пользователя
        """
        async with self.session_factory() as session:
            try:
                energy = await self._get_energy(user_id, session)
                if not energy:
                    energy = await self._create_energy(user_id, session)
                session.add(energy)
                await session.commit()
                return EnergySchema.from_orm(energy)
            except SQLAlchemyError as e:
                logger.error(f"Error getting energy: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})

    async def update_energy(self,
                            user_id: int,
                            amount: int,
                            overmax: bool = False
                            ) -> EnergySchema | JSONResponse:
        """
        Обновляет энергию пользователя
        1. Функция изменяет фактическое количество энергии, после того как проверяет, достаточно ли ее потенциально.
        2. Расчет потенциальной энергии основывается на времени, прошедшем с последнего обновления.
        3. overmax=True надо вызывать только когда происходит добавление энергии больше максимума, например, для покупки
        Args:
            user_id (int): ID пользователя
            amount (int): Изменение количества энергии (может быть отрицательным)
            overmax (bool): Если надо добавить больше максимума энергии(Рекомендуется использовать
            в случае любого *обязательного* повышения энергии, н-р, за просмотр рекламы можно получить 10ед энергии
            если у пользователя 95ед энергии то он получит только 5 единиц если не указать явно overmax=True).
            Т.Е. Если энергию надо повысить, но ее значение не должно превышать 100 единиц, overmax=False
        Returns:
            EnergySchema | JSONResponse: Обновленная энергия, либо JSONResponse с сообщением об ошибке
        """
        async with self.session_factory() as session:
            try:
                energy = await self._get_energy(user_id, session)
                if not energy:
                    await self._create_energy(user_id, session)
                    energy = await self._get_energy(user_id, session)
                now = datetime.now()
                # Прошедшее время с ласт апдейта
                time_passed = now - energy.last_updated
                # Энергия, которая могла бы накопиться если бы прошло game_settings.time_add_one_energy времени
                if energy.overmax:
                    energy_gained = 0
                else:
                    energy_gained = min(
                        time_passed.total_seconds() // game_settings.time_add_one_energy.total_seconds(),
                        self.max_energy)
                # Потенциальное количество энергии которое могло бы накопиться в общем и целом
                potential_energy = min(energy.amount + energy_gained, self.max_energy)
                potential_energy_with_overmax = energy.amount + energy_gained

                if overmax:
                    if amount < 0:
                        return JSONResponse(status_code=400, content={"message": "You should start from 0"})
                    energy.amount = potential_energy_with_overmax + amount
                    energy.overmax = True
                else:
                    if energy.amount < self.max_energy:
                        energy.overmax = False
                    if amount < 0:
                        # Проверяем, достаточно ли энергии для списания
                        if energy.amount + amount < 0:
                            return JSONResponse(status_code=400, content={"message": "Not enough energy"})
                        energy.amount += amount + energy_gained
                    else:
                        # Добавляем энергию, но не превышаем максимум, учитываем что энергии может быть больше чем макс
                        if energy.overmax:
                            energy.amount = potential_energy_with_overmax + amount
                        else:
                            energy.amount = min(potential_energy + amount, self.max_energy)
                energy.last_updated = now

                await session.commit()
                return EnergySchema.from_orm(energy)
            except SQLAlchemyError as e:
                logger.error(f"Error updating energy: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})
