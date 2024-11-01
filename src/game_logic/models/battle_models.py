import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship

from config.database import Base

characters_teams = Table(
    'characters_teams',
    Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id'), primary_key=True)
)


class BattleModel(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    result = Column(String)
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User")
    created_at = Column(DateTime, default=datetime)
    team_1_id = Column(Integer, ForeignKey('teams.id'))
    team_1 = relationship('Team', lazy='joined')
    team_2_id = Column(Integer, ForeignKey('teams.id'))
    team_2 = relationship('Team', lazy='joined')


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    characters = relationship('Character', secondary=characters_teams, lazy='joined')