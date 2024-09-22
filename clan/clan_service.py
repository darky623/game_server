from fastapi import FastAPI, HTTPException
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .models import Clan, SubscribeToClan, RequestToClan, User
from .schemas import ClanSchemaCreate, SubscribeToClanSchemaCreate, \
    RequestToClanSchemaCreate, ClanSchema, SubscribeToClanSchema, \
    RequestToClanSchema, ClanSchemaUpdate

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

                return db_clan

            except IntegrityError as e:
                # Обработка исключения IntegrityError, возникающего при нарушении уникальности
                if 'name' in str(e):
                    raise HTTPException(status_code=400, detail="Clan name already exists")
                else:
                    raise HTTPException(status_code=500, detail="Internal server error")

    async def invite_to_clan(self, clan_id: int, user_id: int, role: str):
        """Отправляет приглашение в клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, которому отправляется приглашение.
            role (str): Роль, предлагаемая пользователю в клане.

        Returns:
            SubscribeToClanSchema: Данные о созданной подписке (приглашении).

        Raises:
            HTTPException:
                - Возникает, если клан не найден.
                - Возникает, если клан является публичным (в публичные кланы нельзя отправлять приглашения).
        """
        async with self.session_factory() as session:
            db_clan = await session.query(Clan).filter(Clan.id == clan_id).first()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            if db_clan.is_public:
                raise HTTPException(status_code=400, detail="Public clan cannot be invited to")

            db_subscribe = SubscribeToClan(
                user_id=user_id,
                clan_id=clan_id,
                role=role,
                status=False
            )
            session.add(db_subscribe)
            await session.commit()
            await session.refresh(db_subscribe)
            return db_subscribe

    async def accept_invite(self, clan_id: int, user_id: int):
        """Принимает приглашение в клан.

        Args:
            clan_id (int): ID клана.
            user_id (int): ID пользователя, принимающего приглашение.

        Returns:
            SubscribeToClanSchema: Данные о подтвержденной подписке.

        Raises:
            HTTPException: Возникает, если приглашение не найдено.
        """
        async with self.session_factory() as session:
            db_subscribe = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == False
            ).first()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="Invitation not found")

            db_subscribe.status = True
            await session.commit()
            await session.refresh(db_subscribe)
            return db_subscribe

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
            db_subscribe = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == False
            ).first()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="Invitation not found")

            await session.delete(db_subscribe)
            await session.commit()
            return {"message": "Invitation declined"}

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
        async with self.session_factory() as session:
            db_subscribe = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == True
            ).first()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(db_subscribe)
            await session.commit()
            return {"message": "User kicked from clan"}

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
            db_subscribe = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == True
            ).first()

            if not db_subscribe:
                raise HTTPException(status_code=404, detail="User not found in clan")

            await session.delete(db_subscribe)
            await session.commit()
            return {"message": "User left clan"}

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
            db_clan = await session.query(Clan).filter(Clan.id == clan_id).first()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            if not db_clan.is_public:
                raise HTTPException(status_code=400, detail="Cannot request to join private clan")

            db_request = RequestToClan(
                user_id=user_id,
                clan_id=clan_id
            )
            session.add(db_request)
            await session.commit()
            await session.refresh(db_request)
            return db_request

    async def confirm_request(self, request_id: int):
        """Подтверждает запрос на вступление в клан.

        Args:
            request_id (int): ID запроса.

        Returns:
            dict: Сообщение об успешном подтверждении запроса.

        Raises:
            HTTPException: Возникает, если запрос не найден.
        """
        async with self.session_factory() as session:
            db_request = await session.query(RequestToClan).filter(RequestToClan.id == request_id).first()
            if not db_request:
                raise HTTPException(status_code=404, detail="Request not found")

            db_request.status = True
            db_subscribe = SubscribeToClan(
                user_id=db_request.user_id,
                clan_id=db_request.clan_id,
                role='Участник',
                status=True
            )

            session.add(db_subscribe)
            await session.delete(db_request)
            await session.commit()
            return {"message": "Request confirmed"}

    async def get_public_clans(self):
        """Возвращает список публичных кланов."""
        async with self.session_factory() as session:
            db_clans = await session.query(Clan).filter(Clan.is_public == True).all()
            return db_clans

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
            db_clan = await session.query(Clan).filter(Clan.id == clan_id).first()
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
            db_members_count = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.status == True
            ).count()
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
            db_clan = await session.query(Clan).filter(Clan.id == clan_id).first()
            if not db_clan:
                raise HTTPException(status_code=404, detail="Clan not found")

            db_subscribe = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == user_id,
                SubscribeToClan.status == True
            ).first()
            if not db_subscribe:
                raise HTTPException(status_code=404, detail="User not found in clan")

            # Проверка прав текущего пользователя
            current_user_role = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.user_id == current_user_id,
                SubscribeToClan.status == True
            ).first()
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
                current_deputies = await session.query(SubscribeToClan).filter(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Заместитель',
                    SubscribeToClan.status == True
                ).count()
                if current_deputies >= 2:
                    raise HTTPException(status_code=400, detail="Maximum number of deputies reached")

            elif new_role == 'Старейшина':
                current_elders = await session.query(SubscribeToClan).filter(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Старейшина',
                    SubscribeToClan.status == True
                ).count()
                if current_elders >= 5:
                    raise HTTPException(status_code=400, detail="Maximum number of elders reached")

            elif new_role == 'Офицер':
                current_officers = await session.query(SubscribeToClan).filter(
                    SubscribeToClan.clan_id == clan_id,
                    SubscribeToClan.role == 'Офицер',
                    SubscribeToClan.status == True
                ).count()
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
            db_members = await session.query(SubscribeToClan).filter(
                SubscribeToClan.clan_id == clan_id,
                SubscribeToClan.status == True
            ).all()
            return db_members
