from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer)
    username = Column(String)
    email = Column(String)
    status = Column(String)
    reg_date = Column(DateTime)
    last_login = Column(DateTime)
    characters = relationship("Character", back_populates="user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="auth_sessions")
    token = Column(String)
    status = Column(String, default='active')
    create_date = Column(DateTime)


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="characters")
    name = Column(String)
    race = Column(String)
    status = Column(String)
