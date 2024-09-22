from sqlalchemy import select
from sqlalchemy.orm import joinedload

from auth.models import User
from chat.schemas import AddChatSchema, ChatSchema
from chat.models import Message, Chat


class ChatService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_chat(self, add_chat: AddChatSchema) -> ChatSchema:
        async with self.session_factory() as session:
            chat = Chat(type=add_chat.type)
            users_query = select(User).where(User.id.in_(add_chat.user_ids))
            result = await session.execute(users_query)
            users = result.scalars().all()

            if not users:
                raise ValueError("Пользователей с такими id не найдено")

            chat.users.extend(users)
            session.add(chat)
            await session.commit()
            chat_response = ChatSchema(id=chat.id,
                                       user_ids=[user.id for user in chat.users],
                                       type=chat.type)
            return chat_response

    async def get_last_messages(self, chat_id: int, quantity: int = 15) -> list[Message]:
        async with self.session_factory() as session:
            stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).limit(quantity)
            result = await session.execute(stmt)
            messages = result.scalars().all()[::-1]
            return messages

    async def get_chat(self, chat_id: int):
        async with self.session_factory() as session:
            result = await session.execute(select(Chat).where(Chat.id == chat_id))
            chat = result.scalars().first()
            return chat

    async def add_message(self, **message_data):
        async with self.session_factory() as session:
            chat_id = message_data.get('chat_id')
            get_chat_stmt = select(Chat).where(Chat.id == chat_id)
            result = await session.execute(get_chat_stmt)
            chat = result.scalars().first()
            if chat is None:
                raise ValueError("Chat not found")

            message = Message(**message_data)
            chat.messages.append(message)
            await session.commit()

    async def check_chat_member(self, chat_id: int, user: User) -> bool:
        chat = await self.get_chat(chat_id)
        if not chat:
            return False
        if chat.type == 'general':
            return True
        for chat_user in chat.users:
            if chat_user.id == user.id:
                return True
        return False

    async def get_general_chat(self) -> Chat:
        async with self.session_factory() as session:
            result = await session.execute(select(Chat).where(Chat.type == 'general'))
            chat = result.scalars().first()
            return chat
