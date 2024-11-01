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

    @staticmethod
    async def _create_energy(user_id: int, session):
        """
        Создает энергию пользователя
        Args:
            user_id (int): ID пользователя
        """
        try:
            energy = Energy(user_id=user_id, amount=game_settings.energy["energy_max"])
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
                    energy is not None and energy.amount == game_settings.energy["energy_max"]
            )

    async def planing_update_energy(self, user_id: int) -> EnergySchema | JSONResponse:
        """
        Обновление энергии на фиксированное количество единиц game_settings.energy_per_time[time_add_one_energy]
         за фиксированное количество времени game_settings.time_add_one_energy
        Args:
            user_id (int): ID пользователя
        Returns:
            EnergySchema: Обновленная энергия
            JSONResponse: Ошибка обновления
        """
        async with self.session_factory() as session:
            energy = await self._get_energy(user_id, session)
            if not energy:
                await self._create_energy(user_id, session)
                energy = await self._get_energy(user_id, session)

            current_time = datetime.now()

            if current_time >= energy.next_update:
                # Присваиваем мин. значение между макс энергией и (текущей энергией юзера+прибавка за 1 единицу времени)
                energy.amount = min(
                    game_settings.energy["energy_max"],
                    energy.amount + game_settings.energy_per_time[time_add_one_energy],
                )
                # Изменяем значение обновление на нынешнее время
                energy.last_updated = current_time
                # Изменяем значение следующего обновления на (текущее время + время за которое прибавляется 1 единица)
                energy.next_update = current_time + game_settings.time_add_one_energy

                if energy.amount == game_settings.energy["energy_max"]:
                    energy.next_update = energy.last_updated

                await session.commit()

            return EnergySchema.from_orm(energy)

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
                logger.error(f"Error gettin energy: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})

    async def update_energy(
            self, user_id: int, amount: int
    ) -> EnergySchema | JSONResponse:
        """
        Обновляет или создает энергию у пользователя
        Args:
            user_id (int): ID пользователя
            amount (int): Изменение количества энергии (может быть отрицательным)
        Returns:
            EnergySchema | JSONResponse: Обновленная энергия, либо JSONResponse с сообщением об ошибке
        """
        async with self.session_factory() as session:
            energy = await self._get_energy(user_id, session)
            if not energy:
                return JSONResponse(
                    status_code=404, content={"message": "Energy not found"}
                )

            # Проверяем, достаточно ли энергии для снятия
            if amount < 0 and abs(amount) > energy.amount:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": f"Insufficient energy. Current energy: {energy.amount}, Requested: {abs(amount)}"}
                )

            new_amount = energy.amount + amount
            energy.amount = max(0, min(new_amount, game_settings.energy["energy_max"]))

            energy.last_updated = datetime.now()
            energy.next_update = datetime.now() + game_settings.time_add_one_energy
            session.add(energy)

            await session.commit()
            return EnergySchema.from_orm(energy)
