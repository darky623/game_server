from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from fastapi.responses import JSONResponse
from config import game_settings
from config.config import dt_format
from src.game_logic.energy.models import Energy
from src.game_logic.energy.schema import EnergySchema
import logging

logger = logging.getLogger(__name__)


class EnergyService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def _create_energy(self, user_id: int):
        """
        Создает энергию пользователя
        Args:
            user_id (int): ID пользователя
        """
        async with self.session_factory() as session:
            energy = Energy(user_id=user_id, amount=game_settings.energy["energy_max"])
            session.add(energy)
            await session.commit()
            return EnergySchema.from_orm(energy)

    async def _get_energy(self, user_id: int):
        async with self.session_factory() as session:
            result = await session.execute(
                select(Energy).where(Energy.user_id == user_id)
            )
            return result.scalars().first()

    async def energy_is_full(self, user_id: int) -> bool:
        """
        Проверяет, заполнена ли энергия пользователя
        Args:
            user_id (int): ID пользователя
        Returns:
            bool: True, если энергия полна, иначе False
        """
        energy = await self._get_energy(user_id)
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
            try:
                energy = await self._get_energy(user_id)
                if not energy:
                    await self._create_energy(user_id)
                    energy = await self._get_energy(user_id)
                energy.amount += game_settings.energy_per_time[
                    game_settings.time_add_one_energy
                ]
                energy.last_updated = datetime.now().strftime(dt_format)
                energy.next_update = (
                    datetime.now() + game_settings.energy["time_add_one_energy"]
                ).strftime(dt_format)
                if energy.amount > game_settings.energy["energy_max"]:
                    energy.amount = game_settings.energy["energy_max"]
                    energy.next_update = energy.last_updated
                await session.commit()
                return EnergySchema.from_orm(energy)
            except Exception as e:
                logger.error(f"Error updating energy for user {user_id}: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})

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
                energy = await self._get_energy(user_id)
                if not energy:
                    return await self._create_energy(user_id)
                await session.add(energy)
                await session.commit()
                return EnergySchema.from_orm(energy)
            except Exception as e:
                logger.error(f"Error getting energy for user {user_id}: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})

    async def update_energy(
        self, user_id: int, amount: int
    ) -> EnergySchema | JSONResponse:
        """
        Обновляет или создает энергию у пользователя
        Args:
            user_id (int): ID пользователя
            amount (int): Новое количество энергии(может быть отрицательным)
        Returns:
            EnergyUpdateSchema | JSONResponse: Обновленная энергия, либо  JSONResponse с сообщением об ошибке
        """
        async with self.session_factory() as session:
            try:
                energy = await self._get_energy(user_id)
                if not energy:
                    return JSONResponse(
                        status_code=404, content={"message": "Energy not found"}
                    )

                energy.amount += amount
                if energy.amount > game_settings.energy["energy_max"]:
                    energy.amount = game_settings.energy["energy_max"]
                elif energy.amount < 0:
                    energy.amount = 0

                energy.last_updated = datetime.now().strftime(dt_format)
                energy.next_update = (
                    datetime.now() + game_settings.energy["time_add_one_energy"]
                ).strftime(dt_format)
                await session.add(energy)

                await session.commit()
                return EnergySchema.from_orm(energy)
            except Exception as e:
                logger.error(f"Error updating energy for user {user_id}: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})


async def handle_exceptions(action):
    try:
        return await action()
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})


def error_handler(func):
    async def wrapper(*args, **kwargs):
        result = await handle_exceptions(lambda: func(*args, **kwargs))
        if isinstance(result, JSONResponse) and result.status_code == 500:
            raise HTTPException(status_code=500, detail=result.content["message"])
        return result

    return wrapper
