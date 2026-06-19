from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    organization_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    owner_id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    data: List[ProjectResponse]
    total: int
    skip: int
    limit: int
