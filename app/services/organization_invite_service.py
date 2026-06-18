from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from app.models.organization_invite import OrganizationInvite, InviteStatus
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.models.user import User
from app.schemas.organization_invite import OrganizationInviteCreate
from app.services.organization_service import check_organization_permission

def create_invite(db: Session, organization_id: int, invite_in: OrganizationInviteCreate, user_id: int) -> OrganizationInvite:
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    acting_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id, OrganizationMember.organization_id == organization_id
    ).first()

    if acting_member and acting_member.role == OrganizationRole.ADMIN and invite_in.role == OrganizationRole.OWNER:
        raise HTTPException(status_code=403, detail="ADMIN cannot invite an OWNER")
    
    # Check if there is already a PENDING invite for this email in this org
    existing_invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.organization_id == organization_id,
        OrganizationInvite.email == invite_in.email,
        OrganizationInvite.status == InviteStatus.PENDING
    ).first()
    
    if existing_invite:
        raise HTTPException(status_code=400, detail="A pending invite already exists for this email in this organization")

    # Check if user is already a member
    user = db.query(User).filter(User.email == invite_in.email).first()
    if user:
        existing_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id
        ).first()
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    invite = OrganizationInvite(
        organization_id=organization_id,
        email=invite_in.email,
        role=invite_in.role,
        expires_at=expires_at,
        status=InviteStatus.PENDING
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite

def list_invites(db: Session, organization_id: int, user_id: int, skip: int = 0, limit: int = 100):
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    invites = (
        db.query(OrganizationInvite)
        .filter(OrganizationInvite.organization_id == organization_id)
        .order_by(OrganizationInvite.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(OrganizationInvite).filter(OrganizationInvite.organization_id == organization_id).count()
    return {"data": invites, "total": total}

def revoke_invite(db: Session, organization_id: int, invite_id: int, user_id: int) -> None:
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.id == invite_id,
        OrganizationInvite.organization_id == organization_id
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
        
    if invite.status != InviteStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot revoke invite with status {invite.status}")
        
    invite.status = InviteStatus.REVOKED
    db.add(invite)
    db.commit()

def accept_invite(db: Session, token: str, user_id: int) -> None:
    invite = db.query(OrganizationInvite).filter(OrganizationInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
        
    if invite.status == InviteStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Invite has already been accepted")
    
    if invite.status == InviteStatus.REVOKED:
        raise HTTPException(status_code=400, detail="Invite has been revoked")
        
    if invite.status == InviteStatus.EXPIRED or invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        invite.status = InviteStatus.EXPIRED
        db.add(invite)
        db.commit()
        raise HTTPException(status_code=400, detail="Invite has expired")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.email.strip().lower() != invite.email.strip().lower():
        raise HTTPException(status_code=403, detail="Invite email does not match user email")
        
    # Create organization member
    existing_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == invite.organization_id,
        OrganizationMember.user_id == user.id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this organization")
        
    member = OrganizationMember(
        organization_id=invite.organization_id,
        user_id=user.id,
        role=invite.role
    )
    
    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(timezone.utc)
    
    db.add(member)
    db.add(invite)
    db.commit()
