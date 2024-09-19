# from sqlalchemy import Column, Integer, String, BINARY, ForeignKey, Boolean
# from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy.orm import relationship
#
# from database import Base
#
#
# class Clan(Base):
#     __tablename__ = "clans"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(25), unique=True, nullable=False)
#     short_name = Column(String(3), unique=True, nullable=False)
#     _avatar = Column(BINARY, nullable=True)
#     chat_id = Column(Integer, ForeignKey("chats.id"))
#     chat = relationship("Chat", backref="clan")
#     rang = Column(Integer, default=0)
#     subscribers = relationship(
#         "Subscribe", backref="clan", cascade="all, delete-orphan"
#     )
#
#     @hybrid_property
#     def avatar(self):
#         """Возвращает изображение в формате Base64"""
#         if self._avatar:
#             return self._avatar.decode("utf-8")
#         return None
#
#     @avatar.setter
#     def avatar(self, value):
#         """Записывает изображение в формате Base64"""
#         if value:
#             self._avatar = value.encode("utf-8")
#         else:
#             self._avatar = None
#
#     def serialize(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "short_name": self.short_name,
#             "avatar": self.avatar,
#             "chat_id": self.chat_id,
#             "rang": self.rang,
#         }
#
#
# class Subscribe(Base):
#     __tablename__ = "subscribers"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     user = relationship("User", backref="subscribers")
#
#     clan_id = Column(Integer, ForeignKey("clans.id"), nullable=True)
#     clan = relationship("Clan", backref="subscribers")
#
#     role = Column(String, nullable=False)
#     status = Column(Boolean, default=False)
#
#     def serialize(self):
#         return {
#             "id": self.id,
#             "user_id": self.user_id,
#             "clan_id": self.clan_id,
#             "role": self.role,
#             "status": self.status,
#         }
