from sqlalchemy import Column, Integer, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship

from database import Base


class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", backref="friends")

    friend_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    friend = relationship("User", backref="friend_requests")

    request_to_add_id = Column(Integer, ForeignKey("request_to_friends.id"), nullable=True)
    request_to_add = relationship("RequestToFriend", backref="friends")

    def serialize(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "friends_id": self.friends_id,
            "chat_id": self.chat_id,
            "request_to_add_id": self.request_to_add_id
        }


class RequestToFriend(Base):
    __tablename__ = "request_to_friends"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender = relationship("User", backref="sent_friend_requests")

    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient = relationship("User", backref="received_friend_requests")

    status = Column(Boolean, default=False)


