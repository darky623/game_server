from sqlalchemy import select

from auth.models import User

from chat.router import chat_service
from friends.models import RequestToFriend, Friend
from friends.schemas import RequestToFriendCreate

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


async def create_private_chat(user_id: int, friend_id: int):
    """Создать приватный чат между двумя пользователями"""
    try:
        new_chat = await chat_service.create_chat(
            type="private", user_ids=[user_id, friend_id]
        )
        return new_chat
    except:
        raise HTTPException(500, "Error creating private chat")


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
    async def _check_existing_friendship(request: RequestToFriendCreate, session):
        """Проверка на существующую дружбу"""
        result = await session.execute(
            select(Friend).where(
                Friend.owner_id == request.sender_id,
                Friend.friend_id == request.recipient_id,
            )
        )
        existing_friend = result.scalars().first()
        if existing_friend:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже является вашим другом",
            )

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
            await self._check_existing_friendship(request, session)

            # Проверка на существование заявки
            existing_request = await self._get_request_by_id(
                request.recipient_id, session
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

    async def accept_friend_request(self, request_id: int) -> JSONResponse:
        """Принять заявку в друзья"""
        async with self.session_factory() as session:
            request = await self._get_request_by_id(request_id, session)
            if request.status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Заявка уже принята"
                )

            request.status = True
            new_friendship = Friend(owner_id=request.sender_id, friend_id=request.recipient_id)
            session.add(new_friendship)
            await session.commit()
        return JSONResponse(
            content={"message": "Заявка принята"}, status_code=status.HTTP_200_OK
        )

    async def cancel_friend_request(self, request_id: int) -> JSONResponse:
        """Отменить отправленную заявку в друзья"""
        async with self.session_factory() as session:
            request = await self._get_request_by_id(request_id, session)
            await session.delete(request)
            await session.commit()
        return JSONResponse(
            content={"message": "Заявка в друзья отменена"},
            status_code=status.HTTP_200_OK,
        )

    async def remove_friend(self, friend_id: int) -> JSONResponse:
        """Удалить из друзей"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Friend).filter(Friend.friend_id == friend_id)
            )
            friend = result.scalar().first()
            if not friend:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Друг не найден"
                )

            await session.delete(friend)
            await session.commit()
            return JSONResponse(
                content={"message": "Друг удален"},
                status_code=status.HTTP_204_NO_CONTENT,
            )

    async def get_friends_list(self, user_id: int) -> list[User]:
        """Получить список друзей"""

        async with self.session_factory() as session:
            result = await session.execute(
                select(Friend)
                .join(User, Friend.owner_id == User.id)
                .filter(Friend.friend_id == user_id)
            )

            friends = result.scalars().all()
            return friends

    async def get_incoming_friend_requests(self, user_id: int) -> list[RequestToFriend]:
        """Получить входящие заявки в друзья"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(RequestToFriend).where(RequestToFriend.recipient_id == user_id)
            )
            incoming_requests = result.scalars().all()
            print(f"Incoming requests for user {user_id}: {incoming_requests}")
            return incoming_requests




