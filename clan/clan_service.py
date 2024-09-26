import logging

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

import config
from .models import Clan, SubscribeToClan, RequestToClan
from schemas import (
    ClanSchemaCreate,
    ClanSchema,
    SubscribeToClanSchema,
    RequestToClanSchema,
    ClanSchemaUpdate,
)

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ClanService:
    """Сервис для управления кланами."""

    def __init__(self, session_factory):
        """Инициализация сервиса с помощью фабрики сессий."""
        self.session_factory = session_factory

    @staticmethod
    async def get_clan_member_limit(clan_id: int, session):
        """Возвращает максимальное количество членов клана в зависимости от ранга.

        Args:
            clan_id (int): ID клана.
            session: Сессия.

        Returns:
            int: Максимальное количество членов клана.

        Raises:
            HTTPException: Возникает, если клан не найден.
        """
        result = await session.execute(select(Clan).where(Clan.id == clan_id))
        db_clan = result.scalar_one_or_none()
        if not db_clan:
            raise HTTPException(status_code=404, detail="Clan not found")

        # Определение лимита по рангу клана
        if db_clan.rang == 1:
            return config.max_of_clan_members_from_rang.get(1)
        elif db_clan.rang == 2:
            return config.max_of_clan_members_from_rang.get(2)
        elif db_clan.rang == 3:
            return config.max_of_clan_members_from_rang.get(3)
        elif db_clan.rang == 4:
            return config.max_of_clan_members_from_rang.get(4)

    @staticmethod
    async def get_clan_members_count(clan_id: int, session):
        """Возвращает текущее количество членов клана - 25, 30, 35, 40.

        Args:
            clan_id (int): ID клана.
            session: Сессия.

        Returns:
            int: Текущее количество членов клана.
        """

        result = await session.execute(
            select(SubscribeToClan).where(SubscribeToClan.clan_id == clan_id)
        )
        db_clan_members = result.scalar().count()
        if not db_clan_members:
            raise HTTPException(status_code=404, detail="Clan not found")

        return db_clan_members

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
                    user_id=user_id, clan_id=db_clan.id, role="Глава", status=True
                )
                session.add(db_subscribe)
                await session.commit()
                await session.refresh(db_subscribe)
                logger.info(f"Clan {db_clan.name} created by user {user_id}")
                return JSONResponse(status_code=201, content=db_clan.serialize())

            except IntegrityError as e:
                # Обработка исключения IntegrityError, возникающего при нарушении уникальности
                if "name" in str(e):
                    raise HTTPException(
                        status_code=400, detail="Clan with this name already exists"
                    )
                else:
                    raise HTTPException(status_code=500, detail="Internal server error")

    async def get_clan_by_id(self, clan_id: int):
        """Возвращает данные клана по его ID.

        Args:
            clan_id (int): ID клана.

        Returns:
            ClanSchema: Данные клана.

        Raises:
            HTTPException: Возникает, если клан не найден.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.id == clan_id))
            db_clan = result.scalar_one_or_none()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")
            return db_clan.serialize()

    async def edit_clan(self, clan_id: int, clan: ClanSchemaUpdate):
        """Редактирует данные клана.

        Args:
            clan_id (int): ID клана.
            clan (ClanSchemaUpdate): Новые данные клана.

        Returns:
            ClanSchema: Обновленные данные клана.

        Raises:
            HTTPException: Возникает, если клан не найден.
        """
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.id == clan_id))
            db_clan = result.scalar_one_or_none()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")
            for field, value in clan:
                setattr(db_clan, field, value)
            await session.commit()
            await session.refresh(db_clan)
            return db_clan.serialize()

    async def get_user_role_in_clan(self, clan_id: int, user_id: int):
        """Получает роль пользователя в клане.

        Args: clan_id (int): ID клана.
            user_id (int): ID пользователя, чью роль нужно узнать.

        Returns:
            str: Роль пользователя в клане.
        """
        async with self.session_factory() as session:
            stmt = select(SubscribeToClan.role).where(
                SubscribeToClan.clan_id == clan_id, SubscribeToClan.user_id == user_id
            )
            result = await session.execute(stmt)
            user_role = result.scalars().first()
            return user_role if user_role else "Participant"

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
                - Возникает, если клан переполнен.
        """
        user_role = await self.get_user_role_in_clan(clan_id, user_id)
        if "invite_users" not in config.permissions_for_clan.get(user_role):
            raise HTTPException(
                status_code=403, detail="You are not allowed to invite users"
            )
        async with self.session_factory() as session:
            # Проверка на факт возможности добавить еще одного участника в клан
            if self.get_clan_member_limit(
                clan_id, session
            ) < self.get_clan_members_count(clan_id, session):
                raise HTTPException(status_code=403, detail="Clan is full")

            new_subscription = SubscribeToClan(
                clan_id=clan_id, user_id=invited_user_id, role="Participant"
            )
            result = await session.execute(
                select(SubscribeToClan)
                .where(SubscribeToClan.clan_id == clan_id)
                .where(SubscribeToClan.user_id == invited_user_id)
            )
            subscription = result.scalars().first()
            if subscription:
                raise HTTPException(
                    status_code=400, detail="User already in clan or invited"
                )

            session.add(new_subscription)
            await session.commit()
            logger.info(
                f"User {user_id} sent invitation to {invited_user_id} to clan {clan_id}"
            )
            return JSONResponse(status_code=201, content=new_subscription.serialize())

    async def accept_invite(self, clan_id: int, user_id: int):
        """Принимает приглашение в клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, принимающего приглашение.

        Returns:
            SubscribeToClanSchema: Данные о подтвержденной подписке.

        Raises:
            HTTPException: Возникает, если приглашение не найдено.
            HTTPException: Возникает, если прав на принятие приглашения нет.
            HTTPException: Возникает, если клан переполнен.
            HTTPException: Возникает, если произошла ошибка на сервере.
        """
        async with self.session_factory() as session:
            try:
                # Проверяем наличие приглашения
                result = await session.execute(
                    select(SubscribeToClan).where(
                        SubscribeToClan.clan_id == clan_id,
                        SubscribeToClan.user_id == user_id,
                        SubscribeToClan.status == False,
                    )
                )
                db_subscribe = result.scalar_one_or_none()

                if not db_subscribe:
                    logging.warning(
                        f"Invitation not found: clan_id={clan_id}, user_id={user_id}"
                    )
                    raise HTTPException(status_code=404, detail="Invitation not found")

                # Проверка на факт возможности добавить еще одного участника в клан
                if self.get_clan_member_limit(
                    clan_id, session
                ) < self.get_clan_members_count(clan_id, session):
                    raise HTTPException(
                        status_code=403, detail="Sorry, this clan is full"
                    )

                # Обновляем статус приглашения на "принято"
                db_subscribe.status = True

                await session.commit()
                await session.refresh(db_subscribe)

                logging.info(
                    f"Invitation accepted: clan_id={clan_id}, user_id={user_id}"
                )
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
            JsonResponse: Сообщение об отклонении приглашения.

        Raises:
            HTTPException: Возникает, если приглашение не найдено.
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.user_id == user_id,
                    SubscribeToClan.status == False,
                )
            )
            db_subscribe = result.scalar_one_or_none()

            if not db_subscribe:
                logger.warning(
                    f"Invitation user: {user_id} in clan: {clan_id} not found"
                )
                raise HTTPException(status_code=404, detail="Invitation not found")

            await session.delete(db_subscribe)
            await session.commit()
            logger.info(f"Invitation declined: {user_id} in clan: {clan_id}")
            return JSONResponse(
                status_code=200, content={"message": "Invitation declined"}
            )

    async def kick_from_clan(self, clan_id: int, kick_user_id: int, user_id: int):
        """Исключает пользователя из клана.

        Args:
            clan_id (int): ID клана.
            kick_user_id (int): ID пользователя, которого нужно исключить.
            user_id (int): ID Текущего пользователя.

        Returns:
            JsonResponse: Сообщение об отклонении приглашения.

        Raises:
            HTTPException: Возникает, если пользователь не найден в клане.
        """
        user_role = await self.get_user_role_in_clan(clan_id, user_id)
        if "kick_users" not in config.permissions_for_clan.get(user_role, []):
            raise HTTPException(
                status_code=403, detail="You are not allowed to kick users"
            )

        async with self.session_factory() as session:
            stmt = select(SubscribeToClan).where(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == kick_user_id,
                SubscribeToClan.status == True,
            )
            result = await session.execute(stmt)
            subscription = result.scalar_one_or_none()

            if not subscription:
                logger.warning(
                    f"User not found in clan: {kick_user_id} in clan: {clan_id}"
                )
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(subscription)
            await session.commit()
            logger.info(f"User kicked from clan: {kick_user_id} in clan: {clan_id}")
            return JSONResponse(
                status_code=200, content={"message": "User kicked from clan"}
            )

    async def leave_clan(self, clan_id: int, user_id: int):
        """Позволяет пользователю выходить из клана.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, который хочет выйти из клана.

        Returns:
            JsonResponse: Сообщение о выходе из клана.

        Raises:
            HTTPException: Возникает, если пользователь не найден в клане.
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.user_id == user_id,
                    SubscribeToClan.status == True,
                )
            )
            db_subscribe = result.scalar_one_or_none()

            if not db_subscribe:
                logger.warning(f"User not found in clan: {user_id} in clan: {clan_id}")
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(db_subscribe)
            await session.commit()
            logger.info(f"User delete from clan: {user_id} in clan: {clan_id}")
            return JSONResponse(
                status_code=200, content={"message": "User delete from clan"}
            )

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
            result = await session.execute(
                select(Clan).where(Clan.id == clan_id, Clan.is_public == True)
            )
        db_clan = result.scalar_one_or_none()
        if not db_clan:
            logger.warning(
                f"Clan not found: {clan_id}, when user: {user_id} wanna join"
            )
            raise HTTPException(status_code=404, detail="Clan not found")

        db_request = RequestToClan(user_id=user_id, clan_id=clan_id)
        session.add(db_request)
        await session.commit()
        await session.refresh(db_request)

        logger.info(f"User: {user_id} send request to clan: {clan_id}")
        return JSONResponse(status_code=201, content=db_request)

    async def confirm_request(self, clan_id: int, accept_user_id: int, user_id: int):
        """Подтверждает запрос на вступление в клан.

        Args:
            clan_id (int): ID запроса.
            accept_user_id (int): ID пользователя, который отправил запрос на вступление.
            user_id (int): ID пользователя, подтверждающего запрос.

        Returns:
            dict: Сообщение об успешном подтверждении запроса.

        Raises:
            HTTPException: Возникает, если запрос не найден.
        """
        async with self.session_factory() as session:
            # Получаем запрос на вступление
            result = await session.execute(
                select(RequestToClan).where(
                    RequestToClan.clan_id == clan_id,
                    RequestToClan.user_id == accept_user_id,
                    RequestToClan.status == False,
                )
            )
            db_request = result.scalar_one_or_none()
            if not db_request:
                raise HTTPException(status_code=404, detail="Request not found")

            # Получаем роль пользователя, который подтверждает запрос
            user_role = await self.get_user_role_in_clan(db_request.clan_id, user_id)
            if "invite_users" not in config.permissions_for_clan.get(user_role, []):
                raise HTTPException(
                    status_code=403, detail="You are not allowed to confirm requests"
                )
            # Проверка на факт возможности добавить еще одного участника в клан
            if self.get_clan_member_limit(clan_id) < self.get_clan_members_count(
                clan_id
            ):
                raise HTTPException(status_code=403, detail="Clan is full")
            # Подтверждаем запрос
            db_request.status = True
            db_subscribe = SubscribeToClan(
                user_id=db_request.user_id,
                clan_id=db_request.clan_id,
                role="Participant",
                status=True,
            )

            session.add(db_subscribe)
            await session.delete(db_request)
            await session.commit()
            return JSONResponse(
                status_code=200, content={"message": "Request confirmed"}
            )

    async def get_public_clans(self):
        """Возвращает список публичных кланов."""
        async with self.session_factory() as session:
            result = await session.execute(select(Clan).where(Clan.is_public == True))
            db_clans = result.scalars().all()
            return db_clans

    async def change_member_role(
        self, clan_id: int, user_id: int, new_role: str, current_user_id: int
    ):
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
            clan = result.scalars().first()
            if not clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            # Проверяем, может ли текущий пользователь назначать роли
            current_user_role = await self.get_user_role_in_clan(
                clan_id, current_user_id
            )

            # Проверка прав для назначения ролей в зависимости от текущей роли пользователя
            allowed_roles_for_roles = {
                "Head": ["Head", "Deputy", "Elder", "Officer"],
                "Deputy": ["Elder", "Officer"],
                "Elder": [],
                "Officer": [],
                "Participant": [],
            }

            if new_role not in allowed_roles_for_roles.get(current_user_role, []):
                raise HTTPException(
                    status_code=403,
                    detail="User does not have permission to assign this role",
                )

            # Проверяем, можно ли назначить новую роль
            if new_role not in config.permissions_for_clan:
                raise HTTPException(status_code=400, detail="Invalid role")

            # Проверяем ограничения на количество людей в каждой роли
            role_limits = {
                "Head": 1,
                "Deputy": 2,
                "Elder": 5,
                "Officer": 5,
                "Participant": self.get_clan_member_limit(clan_id),
            }

            current_roles_count = await session.execute(
                select(SubscribeToClan.role, func.count(SubscribeToClan.id))
                .where(SubscribeToClan.clan_id == clan_id)
                .group_by(SubscribeToClan.role)
            )
            current_roles_count = dict(current_roles_count.all())

            if current_roles_count.get(new_role, 0) >= role_limits[new_role]:
                raise HTTPException(
                    status_code=400, detail=f"Role {new_role} limit reached"
                )

            # Получаем пользователя, которого нужно изменить
            result = await session.execute(
                select(SubscribeToClan)
                .where(SubscribeToClan.clan_id == clan_id)
                .where(SubscribeToClan.user_id == user_id)
            )
            member_subscription = result.scalar_one_or_none()

            if not member_subscription:
                raise HTTPException(status_code=404, detail="Member not found in clan")

            # Меняем роль пользователя
            if new_role == "Head" and current_user_role == "Head":
                current_user_subscription = await session.execute(
                    select(SubscribeToClan)
                    .where(SubscribeToClan.clan_id == clan_id)
                    .where(SubscribeToClan.user_id == current_user_id)
                )
                current_user_role = current_user_subscription.scalar_one_or_none()
                current_user_role.role = "Deputy"
                member_subscription.role = "Head"
            else:
                member_subscription.role = new_role

            await session.commit()
            logger.info(f"Member: {current_user_id} changed role to {new_role} to user: {user_id} in clan: {clan_id}")
            return {"detail": "Member role updated successfully"}

    async def get_clan_members(self, clan_id: int):
        """Возвращает список членов клана."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SubscribeToClan).where(
                    SubscribeToClan.clan_id == clan_id, SubscribeToClan.status == True
                )
            )
            db_members = result.scalars().all()
            return db_members
