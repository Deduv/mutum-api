from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List
from app.models.user import UserStatus


class UserBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    status: UserStatus
    is_super_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    data: List[UserResponse]
    total: int
    skip: int
    limit: int
