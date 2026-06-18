from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.organization_member import OrganizationMember

def check_organization_permission(db: Session, user_id: int, organization_id: int, allowed_roles: list[str]):
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or you don't have access",
        )
    
    if member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough privileges to perform this action",
        )

def check_project_action(db: Session, project, user_id: int, allowed_roles: list[str]):
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == project.organization_id
    ).first()

    if member:
        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough privileges to perform this action",
            )
        return

    if getattr(project, "owner_id", None) == user_id:
        if "OWNER" in allowed_roles:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough privileges to perform this action",
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found or you don't have access",
    )
