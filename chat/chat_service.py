from fastapi import HTTPException
from sqlalchemy import select

import config
from auth.models import User
from chat.schemas import AddChatSchema, ChatSchema
from chat.models import Message, Chat

from clan.router import clan_service


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
            
            session.add(message)
            await session.flush()
            
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

    async def delete_message(self, chat_id: int, message_id: int, user: User):
        chat = await self.get_chat(chat_id)

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        is_clan_chat = chat.type == 'clan'  # Assuming chat type is stored in a type field

        if is_clan_chat:
            # Check permissions for deleting message in clan chat
            user_role = await clan_service.get_user_role_in_clan(chat_id, user.id)
            if 'moderate_chat' not in config.permissions_for_clan.get(user_role, []):
                message = await self.get_message(chat_id, message_id)
                if message.user_id != user.id:
                    raise HTTPException(status_code=403, detail="You are not allowed to delete this message")
        else:
            # Check if user is a member of the chat
            if not await self.check_chat_member(chat_id, user):
                raise HTTPException(status_code=403, detail="You are not allowed to delete this message")

        await self.execute_delete_message(chat_id, message_id)

    async def execute_delete_message(self, chat_id: int, message_id: int):
        async with self.session_factory() as session:
            stmt = select(Message).where(Message.chat_id == chat_id, Message.id == message_id)
            result = await session.execute(stmt)
            message = result.scalars().first()

            if not message:
                raise HTTPException(status_code=404, detail="Message not found")

            await session.delete(message)
            await session.commit()

    async def get_message(self, chat_id: int, message_id: int):
        async with self.session_factory() as session:
            stmt = select(Message).where(Message.chat_id == chat_id, Message.id == message_id)
            result = await session.execute(stmt)
            return result.scalars().first()
