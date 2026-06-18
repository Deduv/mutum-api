from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from app.db.base import Base
from app.models.organization_member import OrganizationRole

class InviteStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class OrganizationInvite(Base):
    __tablename__ = "organization_invites"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, index=True, nullable=False)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)
    token = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()), nullable=False)
    status = Column(SQLEnum(InviteStatus), default=InviteStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
