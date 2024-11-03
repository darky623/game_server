from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class Energy(Base):
    __tablename__ = "energy"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False, default=100)
    last_updated = Column(DateTime, nullable=False, default=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="energy")
