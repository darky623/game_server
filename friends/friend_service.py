from sqlalchemy import select, or_, delete, and_
from sqlalchemy.exc import SQLAlchemyError

from auth.models import User

from chat.router import chat_service
from friends.models import RequestToFriend, Friend
from friends.schemas import (
    RequestToFriendCreate,
    RequestToFriendBase,
    RequestToFriendDelete,
)

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class FriendService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    async def _get_request_by_id(request_id: int, session):
        """Вспомогательная функция для поиска запроса по ID"""
        result = await session.execute(
            select(RequestToFriend).where(RequestToFriend.id == request_id)
        )
        request = result.scalars().first()
        return request

    @staticmethod
    async def _check_existing_friendship(request: RequestToFriendBase, session):
        """Проверка на существующую дружбу"""
        result = await session.execute(
            select(Friend).where(
                Friend.owner_id == request.sender_id,
                Friend.friend_id == request.recipient_id,
            )
        )
        existing_friend = result.scalars().first()
        if existing_friend:
            return True
        return False

    async def send_friend_request(self, request: RequestToFriendCreate) -> JSONResponse:
        """Отправить заявку в друзья"""
        async with self.session_factory() as session:
            # Проверка, что отправитель и получатель не являются одним и тем же пользователем
            if request.sender_id == request.recipient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Невозможно отправить запрос самому себе",
                )

            # Проверка на существующую дружбу
            if await self._check_existing_friendship(request, session):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Этот пользователь уже является Вашим другом",
                )

            # Проверка на существование заявки
            existing_request = await self._get_request_by_id(
                request, session
            )
            if existing_request:
                # Если заявка уже существует, возвращаем сообщение, что заявка уже отправлена
                raise HTTPException(
                    detail="Заявка уже отправлена",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Если заявки не существует, создаем новую заявку
            new_request = RequestToFriend(**request.dict())
            session.add(new_request)
            await session.commit()
            await session.refresh(new_request)
        return JSONResponse(
            content={"message": "Заявка в друзья отправлена"},
            status_code=status.HTTP_201_CREATED,
        )

    async def accept_friend_request(
        self, request_id: int, user_id: int
    ) -> JSONResponse:
        """Принять заявку в друзья"""
        async with self.session_factory() as session:
            request = await self._get_request_by_id(request_id, session)
            if request.recipient_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для принятия этой заявки",
                )
            if request.status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Заявка уже принята"
                )

            request.status = True
            new_friendship = Friend(
                owner_id=request.sender_id, friend_id=request.recipient_id
            )
            session.add(new_friendship)

            # Создаем приватный чат между пользователями
            new_chat = await chat_service.create_chat(
                type="private", user_ids=[user_id, request.sender_id]
            )
            if new_chat:
                session.add(new_chat)

            await session.commit()
        return JSONResponse(
            content={"message": "Заявка принята"}, status_code=status.HTTP_200_OK
        )

    async def cancel_friend_request(self, request_id: int) -> JSONResponse:
        """Отменить отправленную заявку в друзья"""
        async with self.session_factory() as session:
            request = await self._get_request_by_id(request_id, session)
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Запрос не найден"
                )

            if request.status:  # Если заявка уже принята
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Заявка уже принята"
                )
            await session.delete(request)
            await session.commit()
        return JSONResponse(
            content={"message": "Заявка в друзья отменена"},
            status_code=status.HTTP_200_OK,
        )

    async def remove_friend(self, friend_id: int, user_id: int) -> JSONResponse:
        """Удалить из друзей"""
        request = RequestToFriendDelete(sender_id=user_id, recipient_id=friend_id)
        async with self.session_factory() as session:
            if self._check_existing_friendship(request, session):
                try:
                    # Удаляем запись из таблицы Friend
                    await session.execute(
                        delete(Friend).where(
                            or_(
                                and_(
                                    Friend.owner_id == user_id,
                                    Friend.friend_id == friend_id,
                                ),
                                and_(
                                    Friend.owner_id == friend_id,
                                    Friend.friend_id == user_id,
                                ),
                            )
                        )
                    )

                    # Удаляем соответствующую заявку в друзья
                    await session.execute(
                        delete(RequestToFriend).where(
                            or_(
                                and_(
                                    RequestToFriend.sender_id == user_id,
                                    RequestToFriend.recipient_id == friend_id,
                                ),
                                and_(
                                    RequestToFriend.sender_id == friend_id,
                                    RequestToFriend.recipient_id == user_id,
                                ),
                            )
                        )
                    )
                    await session.commit()
                    return JSONResponse(
                        content={"message": "Друг удален"},
                        status_code=status.HTTP_204_NO_CONTENT,
                    )
                except SQLAlchemyError as e:
                    session.rollback()
                    raise HTTPException(
                        400, detail="Произошла ошибка при удалении из друзей: " + str(e)
                    )
            else:
                raise HTTPException(404, detail="Друг не найден")

    async def get_friends_list(self, user_id: int) -> list[User]:
        """Получить список друзей пользователя"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(User)
                .join(
                    Friend, or_(Friend.owner_id == user_id, Friend.friend_id == user_id)
                )
                .filter(or_(User.id == Friend.owner_id, User.id == Friend.friend_id))
            )

            friends = result.scalars().all()

            # Убираем из списка самого пользователя
            friends = [friend for friend in friends if friend.id != user_id]
            friends_list = [{"id": friend.id, "username": friend.username} for friend in friends]

            return friends_list

    async def get_incoming_friend_requests(
        self, user_id: int
    ) -> list[RequestToFriendBase]:
        """Получить входящие заявки в друзья"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(RequestToFriend).where(
                    RequestToFriend.recipient_id == user_id,
                    RequestToFriend.status
                    == False,  # Учитываем только непроверенные заявки
                )
            )
            incoming_requests = result.scalars().all()

            return incoming_requests
