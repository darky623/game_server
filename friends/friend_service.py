from fastapi.openapi.models import Response
from sqlalchemy import select, or_, delete, and_
from sqlalchemy.exc import SQLAlchemyError

from auth.models import User
from chat.models import Chat

from chat.router import chat_service
from chat.schemas import AddChatSchema
from friends.models import RequestToFriend, Friend
from friends.schemas import RequestToFriendBase, RequestToFriendUpdate

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class FriendService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    async def _get_request_by_id(request_id: int, session):
        """Вспомогательная функция для поиска запроса по ID"""
        try:
            result = await session.execute(
                select(RequestToFriend).where(RequestToFriend.id == request_id)
            )
            request = result.scalars().first()
            return request
        except SQLAlchemyError:
            return None

    @staticmethod
    async def _check_existing_friendship(friend_id: int, user_id: int, session):
        """Проверка на существующую дружбу"""
        result = await session.execute(
            select(Friend).where(
                Friend.owner_id == user_id,
                Friend.friend_id == friend_id,
            )
        )
        existing_friend = result.scalars().first()
        if existing_friend:
            return True
        return False

    async def send_friend_request(self, friend_id: int, user_id: int) -> JSONResponse:
        """Отправить заявку в друзья"""
        try:
            async with self.session_factory() as session:
                # Проверка, что отправитель и получатель не являются одним и тем же пользователем
                if user_id == friend_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Невозможно отправить запрос самому себе",
                    )

                # Проверка на существующую дружбу
                if await self._check_existing_friendship(user_id, friend_id, session):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Этот пользователь уже является Вашим другом",
                    )

                # Проверка на существование заявки
                request_id = await session.execute(
                    select(RequestToFriend.id).where(
                        and_(
                            RequestToFriend.sender_id == user_id,
                            RequestToFriend.recipient_id == friend_id,
                        )
                    )
                )
                existing_request = await self._get_request_by_id(request_id, session)
                if existing_request:
                    # Если заявка уже существует, возвращаем сообщение, что заявка уже отправлена
                    raise HTTPException(
                        detail="Заявка уже отправлена",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                # Если заявки не существует, создаем новую заявку
                new_request = RequestToFriend(sender_id=user_id, recipient_id=friend_id)
                session.add(new_request)
                await session.commit()
                await session.refresh(new_request)

            return JSONResponse(
                content={"message": "Заявка в друзья отправлена"},
                status_code=status.HTTP_201_CREATED,
            )
        except SQLAlchemyError as e:
            raise e

    async def accept_friend_request(
            self, request: RequestToFriendUpdate, user_id: int
    ) -> JSONResponse:
        """Принять заявку в друзья"""
        try:
            async with self.session_factory() as session:
                print(request.id, user_id, "----------------------------------------")
                result = await session.execute(
                    select(RequestToFriend).where(
                        RequestToFriend.id == request.id,
                        RequestToFriend.recipient_id == user_id,
                        RequestToFriend.status == False
                    )
                )
                request = result.scalars().first()
                if request is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Запрос не найден"
                    )
                elif request.recipient_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вас нет прав для принятия этой заявки",
                    )
                else:
                    request.status = True

                new_friendship = Friend(
                    owner_id=user_id, friend_id=request.sender_id
                )
                session.add(new_friendship)
                await session.delete(request)
                # # Создаем приватный чат между пользователями
                # new_chat = await chat_service.create_chat(
                #     AddChatSchema(
                #         type="private",
                #         user_ids=[user_id, friend_id],
                #     )
                # )
                #
                # if new_chat is None:
                #     raise HTTPException(
                #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                #         detail="Не удалось создать чат",
                #     )
                # chat_service.add_chat(
                #     AddChatSchema(
                #         name="chat",
                #         users=[user_id, friend_id],
                #         chat_id=new_chat.id)
                # )
                #
                # session.add(new_chat)

                await session.commit()
            return JSONResponse(
                content={"message": "Заявка принята"}, status_code=status.HTTP_200_OK
            )

        except SQLAlchemyError as e:
            raise e

    async def cancel_friend_request(self, request_id: int, user_id: int) -> JSONResponse:
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
            if request.sender_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для отмены этой заявки",
                )
            await session.delete(request)
            await session.commit()
        return JSONResponse(
            content={"message": "Заявка в друзья отменена"},
            status_code=status.HTTP_200_OK,
        )

    async def remove_friend(self, friend_id: int, user_id: int) -> Response:
        """Удалить из друзей"""
        async with self.session_factory() as session:
            if self._check_existing_friendship(friend_id, user_id, session):
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
                    return Response(status_code=204)

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

            friends = result.scalars().unique().all()

            # Убираем из списка самого пользователя
            friends = [friend for friend in friends if friend.id != user_id]
            friends_list = [{"id": friend.id, "username": friend.username} for friend in friends]

            return friends_list

    async def get_coming_friend_requests(
            self, user_id: int
    ) -> list[RequestToFriendBase]:
        """Получить исходящие заявки в друзья"""
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

    async def get_all_incoming_requests(self, user_id: int) -> list[RequestToFriendBase]:
        """Получить входящие заявки в друзья"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(RequestToFriend).where(
                    RequestToFriend.sender_id == user_id,
                    RequestToFriend.status
                    == False,  # Учитываем только непроверенные заявки
                )
            )
            incoming_requests = result.scalars().all()

            return incoming_requests
