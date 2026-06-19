from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.organization_member import OrganizationRole

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    name: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationListResponse(BaseModel):
    data: List[OrganizationResponse]
    total: int
    skip: int
    limit: int

class OrganizationMemberBase(BaseModel):
    role: OrganizationRole

class OrganizationMemberCreate(OrganizationMemberBase):
    user_id: int

class OrganizationMemberUpdate(OrganizationMemberBase):
    pass

class OrganizationMemberResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: OrganizationRole
    joined_at: datetime
    name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True

class OrganizationMemberListResponse(BaseModel):
    data: List[OrganizationMemberResponse]
    total: int
