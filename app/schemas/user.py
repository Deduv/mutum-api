from pydantic import BaseModel, ConfigDict, field_validator
import re
from datetime import datetime
from typing import Optional, List
from app.models.user import UserStatus


class UserBase(BaseModel):
    name: Optional[str] = None
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    status: UserStatus
    is_super_admin: bool
    is_email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    data: List[UserResponse]
    total: int
    skip: int
    limit: int
