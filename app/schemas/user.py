from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.user import UserStatus


class UserBase(BaseModel):
    name: Optional[str] = None
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    status: UserStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    data: List[UserResponse]
    total: int
    skip: int
    limit: int
