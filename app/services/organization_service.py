from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationMemberCreate,
    OrganizationMemberUpdate
)
from app.core.rbac import check_organization_permission

def create_organization(db: Session, org_in: OrganizationCreate, user_id: int) -> Organization:
    db_org = Organization(name=org_in.name)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    db_member = OrganizationMember(
        user_id=user_id,
        organization_id=db_org.id,
        role=OrganizationRole.OWNER
    )
    db.add(db_member)
    db.commit()

    return db_org

def get_organization(db: Session, organization_id: int, user_id: int) -> Organization:
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN", "MEMBER"])
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    return org

def update_organization(db: Session, organization_id: int, org_in: OrganizationUpdate, user_id: int) -> Organization:
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    if org_in.name is not None:
        org.name = org_in.name
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

def delete_organization(db: Session, organization_id: int, user_id: int) -> None:
    check_organization_permission(db, user_id, organization_id, ["OWNER"])
    
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    from app.models.project import Project
    projects_count = db.query(Project).filter(Project.organization_id == organization_id).count()
    if projects_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete organization with existing projects")
        
    members_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id).count()
    if members_count > 1:
        raise HTTPException(status_code=400, detail="Cannot delete organization with extra members")
        
    # Delete invites
    from app.models.organization_invite import OrganizationInvite
    db.query(OrganizationInvite).filter(OrganizationInvite.organization_id == organization_id).delete()
    
    # Delete the single owner member first, then the org
    member = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id).first()
    if member:
        db.delete(member)
        
    db.delete(org)
    db.commit()

def list_organizations(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    orgs = (
        db.query(Organization)
        .join(OrganizationMember)
        .filter(OrganizationMember.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return orgs

def count_organizations(db: Session, user_id: int) -> int:
    return (
        db.query(Organization)
        .join(OrganizationMember)
        .filter(OrganizationMember.user_id == user_id)
        .count()
    )

def list_members(db: Session, organization_id: int, user_id: int):
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN", "MEMBER"])
    from sqlalchemy.orm import joinedload
    members = db.query(OrganizationMember).options(joinedload(OrganizationMember.user)).filter(OrganizationMember.organization_id == organization_id).all()
    
    enriched_members = []
    for m in members:
        enriched_members.append({
            "id": m.id,
            "user_id": m.user_id,
            "organization_id": m.organization_id,
            "role": m.role,
            "joined_at": m.joined_at,
            "name": m.user.name if m.user else None,
            "email": m.user.email if m.user else ""
        })
    return enriched_members

def add_member(db: Session, organization_id: int, member_in: OrganizationMemberCreate, user_id: int):
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    from app.models.user import User
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == member_in.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    acting_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id, OrganizationMember.organization_id == organization_id
    ).first()
    
    if member_in.role == OrganizationRole.OWNER and acting_member.role != OrganizationRole.OWNER:
        raise HTTPException(status_code=403, detail="Only OWNER can add another OWNER")

    new_member = OrganizationMember(
        user_id=member_in.user_id,
        organization_id=organization_id,
        role=member_in.role
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    # Enrich
    user = db.query(User).filter(User.id == new_member.user_id).first()
    return {
        "id": new_member.id,
        "user_id": new_member.user_id,
        "organization_id": new_member.organization_id,
        "role": new_member.role,
        "joined_at": new_member.joined_at,
        "name": user.name if user else None,
        "email": user.email if user else ""
    }

def update_member_role(db: Session, organization_id: int, target_user_id: int, member_in: OrganizationMemberUpdate, user_id: int):
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    acting_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id, OrganizationMember.organization_id == organization_id
    ).first()
    
    from sqlalchemy.orm import joinedload
    target_member = db.query(OrganizationMember).options(joinedload(OrganizationMember.user)).filter(
        OrganizationMember.user_id == target_user_id, OrganizationMember.organization_id == organization_id
    ).first()
    
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if acting_member.role == OrganizationRole.ADMIN:
        if target_member.role == OrganizationRole.OWNER:
            raise HTTPException(status_code=403, detail="ADMIN cannot change role of an OWNER")
        if member_in.role == OrganizationRole.OWNER:
            raise HTTPException(status_code=403, detail="ADMIN cannot promote someone to OWNER")

    # If an OWNER is being demoted, ensure they are not the last OWNER
    if target_member.role == OrganizationRole.OWNER and member_in.role != OrganizationRole.OWNER:
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.role == OrganizationRole.OWNER
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last OWNER of the organization")

    target_member.role = member_in.role
    db.add(target_member)
    db.commit()
    db.refresh(target_member)
    
    return {
        "id": target_member.id,
        "user_id": target_member.user_id,
        "organization_id": target_member.organization_id,
        "role": target_member.role,
        "joined_at": target_member.joined_at,
        "name": target_member.user.name if target_member.user else None,
        "email": target_member.user.email if target_member.user else ""
    }

def remove_member(db: Session, organization_id: int, target_user_id: int, user_id: int):
    check_organization_permission(db, user_id, organization_id, ["OWNER", "ADMIN"])
    
    acting_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id, OrganizationMember.organization_id == organization_id
    ).first()
    
    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == target_user_id, OrganizationMember.organization_id == organization_id
    ).first()
    
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found")

    if acting_member.role == OrganizationRole.ADMIN and target_member.role == OrganizationRole.OWNER:
        raise HTTPException(status_code=403, detail="ADMIN cannot remove an OWNER")
        
    if target_member.role == OrganizationRole.OWNER:
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.role == OrganizationRole.OWNER
        ).count()
        if owner_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last OWNER of the organization")

    db.delete(target_member)
    db.commit()
