from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import game_settings
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
        self.time_add_one_energy = game_settings.time_add_one_energy.total_seconds()

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

    async def get_energy(self, user_id: int, session: Session) -> Energy | JSONResponse:
        """
        Возвращает энергию пользователя, если ее нет - создаёт энергию
        Args:
            user_id (int): ID пользователя
            session (Session): сессия
        Returns:
            EnergySchema: Энергия пользователя
        """
        try:
            energy = await self._get_energy(user_id, session)
            if not energy:
                energy = await self._create_energy(user_id, session)
            return energy
        except SQLAlchemyError as e:
            logger.error(f"Error getting energy: {e}")
            return JSONResponse(status_code=500, content={"message": str(e)})

    async def update_energy(
        self, user_id: int, amount: int, overmax: bool = False
    ) -> EnergySchema | JSONResponse:
        """
        Обновляет энергию пользователя
        1. Функция изменяет фактическое количество энергии, после того как проверяет, достаточно ли ее потенциально.
        2. Расчет потенциальной энергии основывается на времени, прошедшем с последнего обновления.
        3. overmax=True надо вызывать только когда происходит добавление энергии больше максимума, н-р, для покупки
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
                energy = await self.get_energy(user_id, session)
                if isinstance(energy, JSONResponse):
                    return energy

                # Расчет потенциальной энергии
                potential_energy, potential_energy_with_overmax = (
                    await self._calculate_potential_energy(energy)
                )

                # Обновление энергии
                energy = await self._process_energy_update(
                    energy,
                    amount,
                    overmax,
                    potential_energy,
                    potential_energy_with_overmax,
                )
                # Обработка исключений
                if isinstance(energy, JSONResponse):
                    return energy

                # Проверяем, если энергия больше максимума, то переводим овермакс энергии в True
                energy = await self._check_and_correct_overmax(energy)
                energy.last_updated = datetime.now()
                session.add(energy)
                await session.commit()
                return EnergySchema.from_orm(energy)
            except SQLAlchemyError as e:
                logger.error(f"Error updating energy: {e}")
                return JSONResponse(status_code=500, content={"message": str(e)})

    async def _calculate_potential_energy(self, energy: Energy) -> tuple[int, int]:
        """Расчет потенциальной энергии

        Args:
            energy (Energy): Объект энергии пользователя

        Returns:
            tuple[int, int]: потенциальное количество энергии и потенциальное количество энергии с овермаксом
        """
        now = datetime.now()
        # Прошедшее время с ласт апдейта
        time_passed = (now - energy.last_updated).total_seconds()
        # Энергия, которая могла бы накопиться если бы прошло game_settings.time_add_one_energy времени
        if energy.overmax:
            energy_gained = 0
        else:
            energy_gained = min(
                time_passed // self.time_add_one_energy, self.max_energy
            )
        # Потенциальное количество энергии которое могло бы накопиться если бы она тикала каждую ед. времени
        potential_energy = min(energy.amount + energy_gained, self.max_energy)
        # Потенциальное количество энергии если у поль-ля потенциально станет больше чем максимум энергии, после обновы
        potential_energy_with_overmax = energy.amount + min(energy_gained, abs(energy.amount-self.max_energy))

        return potential_energy, potential_energy_with_overmax

    async def _check_and_correct_overmax(self, energy: Energy) -> Energy:
        """
        Проверяет, если энергия больше максимума, то переводит овермакс в True

        Args:
            energy (Energy): Объект энергии пользователя
        """
        energy.overmax = energy.amount > self.max_energy
        return energy

    async def _process_energy_update(
        self,
        energy: Energy,
        amount: int,
        overmax: bool,
        potential_energy: int,
        potential_energy_with_overmax: int,
    ) -> Energy | JSONResponse:
        """
        Обрабатывает логику обновления энергии в зависимости от переданных параметров.

        Args:
            energy (Energy): Объект энергии пользователя
            amount (int): Изменение количества энергии
            overmax (bool): Флаг, указывающий на возможность превышения максимума
            potential_energy (int): Потенциальное количество энергии
            potential_energy_with_overmax (int): Потенциальное количество энергии с овермаксом
        Returns:
            EnergySchema | JSONResponse: Обновленная энергия или сообщение об ошибке
        """

        if overmax:
            return await self._handle_overmax_energy(
                energy, amount, potential_energy_with_overmax
            )
        else:
            return await self._handle_regular_energy(
                energy, amount, potential_energy, potential_energy_with_overmax
            )

    async def _handle_overmax_energy(
        self, energy: Energy, amount: int, potential_energy_with_overmax: int
    ) -> Energy | JSONResponse:
        """
        Обрабатывает случай, когда пользователь может иметь энергию больше максимума.
        Args:
            energy (Energy): Объект энергии пользователя
            amount (int): Изменение количества энергии
            potential_energy_with_overmax (int): Потенциальное количество энергии с овермаксом
        Returns:
            EnergySchema | JSONResponse: Обновленная энергия или сообщение об ошибке
        """
        # Запрещаем отнимать энергию если овермакс передаваемый в функцию == True
        if amount < 0:
            return JSONResponse(
                status_code=400,
                content={"message": "You should start from 0"},
            )
        # Добавляем энергию
        energy.amount = potential_energy_with_overmax + amount

        return energy

    async def _handle_regular_energy(
        self,
        energy: EnergySchema,
        amount: int,
        potential_energy: int,
        potential_energy_with_overmax: int,
    ) -> EnergySchema | JSONResponse:
        """
        Обрабатывает случай обычного обновления энергии.
        Args:
            energy (Energy): Объект энергии пользователя
            amount (int): Изменение количества энергии
            potential_energy (int): Потенциальное количество энергии
            potential_energy_with_overmax (int): Потенциальное количество энергии с овермаксом
        Returns:
            EnergySchema | JSONResponse: Обновленная энергия или сообщение об ошибке
        """
        # Вычитание энергии
        if amount < 0:
            # Проверяем, достаточно ли энергии для списания(больше 100 списать нельзя)
            if potential_energy_with_overmax + amount < 0:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Not enough energy"},
                )
            # Списываем энергию
            if energy.overmax:
                energy.amount = potential_energy_with_overmax + amount
            else:
                energy.amount = potential_energy + amount
        # Добавление энергии
        else:
            # Не превышаем максимум, учитываем что энергии может быть больше чем макс
            if energy.overmax:
                energy.amount += amount
            else:
                energy.amount = min(potential_energy + amount, self.max_energy)
        return energy
