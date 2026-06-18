from pydantic import BaseModel, field_validator
import re
from typing import Optional
from datetime import datetime
from app.models.organization_member import OrganizationRole
from app.models.organization_invite import InviteStatus

class OrganizationInviteBase(BaseModel):
    email: str
    role: OrganizationRole = OrganizationRole.MEMBER

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v

class OrganizationInviteCreate(OrganizationInviteBase):
    pass

class OrganizationInviteResponse(OrganizationInviteBase):
    id: int
    organization_id: int
    token: str
    status: InviteStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

class OrganizationInviteListResponse(BaseModel):
    data: list[OrganizationInviteResponse]
    total: int

