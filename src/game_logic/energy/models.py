from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from datetime import datetime

Base = declarative_base()


class Energy(Base):
    __tablename__ = "energy"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False, default=100)
    last_updated = Column(DateTime, nullable=False, default=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="energy")
