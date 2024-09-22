import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

import config
from models import Clan, SubscribeToClan, RequestToClan
from schemas import ClanSchemaCreate, ClanSchema, SubscribeToClanSchema, \
    RequestToClanSchema

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ClanService:
    """Сервис для управления кланами."""

    def __init__(self, session_factory):
        """Инициализация сервиса с помощью фабрики сессий."""
        self.session_factory = session_factory

    async def create_clan(self, clan: ClanSchemaCreate, user_id: int):
        """Создает новый клан.

        Args:
            clan (ClanSchemaCreate): Данные для создания клана.
            user_id (int): ID пользователя, создающего клан.

        Returns:
            ClanSchema: Данные созданного клана.

        Raises:
            HTTPException: Возникает, если имя или короткое имя клана уже заняты.
        """
        async with self.session_factory() as session:
            try:
                db_clan = Clan(**clan.dict())
                db_clan.user_id = user_id
                session.add(db_clan)
                await session.commit()
                await session.refresh(db_clan)

                # Создаем подписку для создателя клана с ролью "Глава"
                db_subscribe = SubscribeToClan(
                    user_id=user_id,
                    clan_id=db_clan.id,
                    role='Глава',
                    status=True
                )
                session.add(db_subscribe)
                await session.commit()
                await session.refresh(db_subscribe)
                logger.info(f"Clan {db_clan.name} created by user {user_id}")
                return JSONResponse(status_code=201, content=db_clan.serialize())

            except IntegrityError as e:
                # Обработка исключения IntegrityError, возникающего при нарушении уникальности
                if 'name' in str(e):
                    raise HTTPException(status_code=400, detail="Clan name already exists")
                else:
                    raise HTTPException(status_code=500, detail="Internal server error")

    async def get_user_role_in_clan(self, clan_id: int, user_id: int):
        """Получает роль пользователя в клане.

        Args: clan_id (int): ID клана.
            user_id (int): ID пользователя, чью роль нужно узнать.

        Returns:
            str: Роль пользователя в клане.
        """
        async with self.session_factory() as session:
            stmt = select(SubscribeToClan.role).where(SubscribeToClan.clan_id == clan_id,
                                                      SubscribeToClan.user_id == user_id)
            result = await session.execute(stmt)
            user_role = result.scalars().first()
            return user_role if user_role else 'Participant'

    async def invite_to_clan(self, clan_id: int, invited_user_id: int, user_id: int):
        """Отправляет приглашение в клан.

        Args:
            clan_id (int): ID клана.
            invited_user_id (int): ID пользователя, которого приглашают.
            user_id (int): ID пользователя, от которого отправляется приглашение.

        Returns:
            SubscribeToClanSchema: Данные о созданной подписке (приглашении).

        Raises:
            HTTPException:
                - Возникает, если прав на приглашение нет.
        """
        user_role = await self.get_user_role_in_clan(clan_id, user_id)
        if 'invite_users' not in config.permissions_for_clan.get(user_role, []):
            raise HTTPException(status_code=403, detail="You are not allowed to invite users")

        async with self.session_factory() as session:
            subscription = SubscribeToClan(clan_id=clan_id, user_id=invited_user_id, role='Participant')
            session.add(subscription)
            await session.commit()
            logger.info(f"User {user_id} sent invitation to {invited_user_id} to clan {clan_id}")
            return JSONResponse(status_code=201, content=subscription.serialize())

    async def accept_invite(self, clan_id: int, user_id: int):
        """Принимает приглашение в клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, принимающего приглашение.

        Returns:
            SubscribeToClanSchema: Данные о подтвержденной подписке.

        Raises:
            HTTPException: Возникает, если приглашение не найдено.
            HTTPException: Возникает, если произошла ошибка на сервере.
        """
        async with self.session_factory() as session:
            try:
                # Проверяем наличие приглашения
                result = await session.execute(select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.user_id == user_id,
                    SubscribeToClan.status == False
                ))
                db_subscribe = result.scalar_one_or_none()

                if not db_subscribe:
                    logging.warning(f"Invitation not found: clan_id={clan_id}, user_id={user_id}")
                    raise HTTPException(status_code=404, detail="Invitation not found")

                # Обновляем статус приглашения на "принято"
                db_subscribe.status = True
                await session.commit()
                await session.refresh(db_subscribe)

                logging.info(f"Invitation accepted: clan_id={clan_id}, user_id={user_id}")
                return JSONResponse(status_code=200, content=db_subscribe.serialize())

            except HTTPException as e:
                logging.error(f"Error while accepting invitation: {e}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

    async def decline_invite(self, clan_id: int, user_id: int):
        """Отклоняет приглашение в клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, отклоняющего приглашение.

        Returns:
            dict: Сообщение об успешном отклонении приглашения.

        Raises:
            HTTPException: Возникает, если приглашение не найдено.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == False
            ))
            db_subscribe = result.scalar_one_or_none()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="Invitation not found")

            await session.delete(db_subscribe)
            await session.commit()
            return JSONResponse(status_code=200, content={"message": "Invitation declined"})

    async def kick_from_clan(self, clan_id: int, user_id: int):
        """Исключает пользователя из клана.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, которого нужно исключить.

        Returns:
            dict: Сообщение об успешном исключении пользователя.

        Raises:
            HTTPException: Возникает, если пользователь не найден в клане.
        """
        user_role = await self.get_user_role_in_clan(clan_id, user_id)
        if 'kick_users' not in config.permissions_for_clan.get(user_role, []):
            raise HTTPException(status_code=403, detail="You are not allowed to kick users")

        async with self.session_factory() as session:
            stmt = select(SubscribeToClan).where(SubscribeToClan.clan_id == clan_id, SubscribeToClan.user_id == kicked_user_id)
            result = await session.execute(stmt)
            subscription = result.scalars().first()

            if not subscription:
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(subscription)
            await session.commit()
            return JSONResponse(status_code=200, content={"message": "User kicked from clan"})

    async def leave_clan(self, clan_id: int, user_id: int):
        """Удаляет пользователя из клана.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, который хочет выйти из клана.

        Returns:
            dict: Сообщение об успешном выходе из клана.

        Raises:
            HTTPException: Возникает, если пользователь не найден в клане.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == True
            ))
            db_subscribe = result.scalar_one_or_none()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(db_subscribe)
            await session.commit()
            return JSONResponse(status_code=200, content={"message": "User delete from clan"})

    async def request_to_clan(self, clan_id: int, user_id: int):
        """Отправляет запрос на вступление в публичный клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, отправляющего запрос.

        Returns:
            RequestToClanSchema: Данные о созданном запросе.

        Raises:
            HTTPException:
                - Возникает, если клан не найден.
                - Возникает, если клан является приватным.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.id == clan_id,
                                                              Clan.is_public == True))
            db_clan = result.scalar_one_or_none()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            db_request = RequestToClan(
                user_id=user_id,
                clan_id=clan_id
            )
            session.add(db_request)
            await session.commit()
            await session.refresh(db_request)
            return db_request

    async def confirm_request(self, request_id: int, user_id: int):
        """Подтверждает запрос на вступление в клан.

        Args:
            request_id (int): ID запроса.
            user_id (int): ID пользователя, подтверждающего запрос.

        Returns:
            dict: Сообщение об успешном подтверждении запроса.

        Raises:
            HTTPException: Возникает, если запрос не найден.
        """
        async with self.session_factory() as session:
            # Получаем запрос на вступление
            result = await session.execute(select(RequestToClan).where(RequestToClan.id == request_id))
            db_request = result.scalar_one_or_none()
            if not db_request:
                raise HTTPException(status_code=404, detail="Request not found")

            # Получаем роль пользователя, который подтверждает запрос
            user_role = await self.get_user_role_in_clan(db_request.clan_id, user_id)
            if 'invite_users' not in config.permissions_for_clan.get(user_role, []):
                raise HTTPException(status_code=403, detail="You are not allowed to confirm requests")

            # Подтверждаем запрос
            db_request.status = True
            db_subscribe = SubscribeToClan(
                user_id=db_request.user_id,
                clan_id=db_request.clan_id,
                role='Participant',
                status=True
            )

            session.add(db_subscribe)
            await session.delete(db_request)
            await session.commit()
            return JSONResponse(status_code=200, content={"message": "Request confirmed"})

    async def get_public_clans(self):
        """Возвращает список публичных кланов."""
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.is_public == True))
            db_clans = result.scalars().all()
            return db_clans

    # TODO
    async def get_clan_member_limit(self, clan_id: int):
        """Возвращает максимальное количество членов клана в зависимости от ранга.

        Args:
            clan_id (int): ID клана.

        Returns:
            int: Максимальное количество членов клана.

        Raises:
            HTTPException: Возникает, если клан не найден.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.id == clan_id))
            db_clan = result.scalar_one_or_none()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            # Определение лимита по рангу клана
            if db_clan.rang == 1:
                return 25
            elif db_clan.rang == 2:
                return 30
            elif db_clan.rang == 3:
                return 35
            elif db_clan.rang == 4:
                return 40
            else:
                return 20

    async def get_clan_members_count(self, clan_id: int):
        """Возвращает текущее количество членов клана.

        Args:
            clan_id (int): ID клана.

        Returns:
            int: Текущее количество членов клана.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.status == True
            ))
            db_members_count = result.scalars().count()
            return db_members_count

    async def change_member_role(self, clan_id: int, user_id: int, new_role: str, current_user_id: int):
        """Изменяет роль члена клана.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, чья роль изменяется.
            new_role (str): Новая роль.
            current_user_id (int): ID пользователя, изменяющего роль.

        Returns:
            SubscribeToClanSchema: Данные о пользователе с обновленной ролью.

        Raises:
            HTTPException:
                - Возникает, если клан не найден.
                - Возникает, если пользователь не найден в клане.
                - Возникает, если текущий пользователь не имеет прав на изменение роли.
                - Возникает, если указана неверная роль.
                - Возникает, если достигнут лимит на количество пользователей с определенной ролью.
                - Возникает, если пытаются назначить лидером не того пользователя.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.id == clan_id))
            db_clan = result.scalar_one_or_none()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == True
            ))
            db_subscribe = result.scalar_one_or_none()
            if not db_subscribe:
                raise HTTPException(status_code=404, detail="User not found in clan")

            # Проверка прав текущего пользователя
            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == current_user_id,
                SubscribeToClan.status == True
            ))
            current_user_role = result.scalar_one_or_none()
            if not current_user_role:
                raise HTTPException(status_code=403, detail="You are not a member of this clan")

            if current_user_role.role not in ('Глава', 'Заместитель'):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            # Проверка доступности роли
            if new_role not in ('Глава', 'Заместитель', 'Старейшина', 'Офицер', 'Участник'):
                raise HTTPException(status_code=400, detail="Invalid role")

            # Проверка лимита на роли
            if new_role == 'Глава':
                if await self.get_clan_members_count(clan_id) > 1 or db_subscribe.user_id != current_user_id:
                    raise HTTPException(status_code=400, detail="Only clan leader can be assigned as leader")

            elif new_role == 'Заместитель':
                result = await session.execute(select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Заместитель',
                    SubscribeToClan.status == True
                ))
                current_deputies = result.scalars().count()
                if current_deputies >= 2:
                    raise HTTPException(status_code=400, detail="Maximum number of deputies reached")

            elif new_role == 'Старейшина':
                result = await session.execute(select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Старейшина',
                    SubscribeToClan.status == True
                ))
                current_elders = result.scalars().count()
                if current_elders >= 5:
                    raise HTTPException(status_code=400, detail="Maximum number of elders reached")

            elif new_role == 'Офицер':
                result = await session.execute(select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Офицер',
                    SubscribeToClan.status == True
                ))
                current_officers = result.scalars().count()
                if current_officers >= 5:
                    raise HTTPException(status_code=400, detail="Maximum number of officers reached")

            # Обновление роли
            db_subscribe.role = new_role
            await session.commit()
            await session.refresh(db_subscribe)
            return db_subscribe

    async def get_clan_members(self, clan_id: int):
        """Возвращает список членов клана."""
        async with self.session_factory() as session:
            result = await session.execute(select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.status == True
            ))
            db_members = result.scalars().all()
            return db_members
