from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from sqlalchemy import Enum as SQLEnum
from app.db.base import Base

class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, server_default=UserStatus.ACTIVE.value, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    assigned_tasks = relationship("Task", back_populates="assigned_user")
