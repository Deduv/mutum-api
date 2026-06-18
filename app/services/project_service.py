from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.project import Project
from app.models.organization_member import OrganizationMember
from app.schemas.project import ProjectCreate, ProjectUpdate
from sqlalchemy import or_
from app.core.rbac import check_project_action, check_organization_permission

def _get_user_organization_ids(db: Session, user_id: int) -> list[int]:
    members = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
    return [m.organization_id for m in members]

def _get_user_personal_workspace_id(db: Session, user_id: int) -> Optional[int]:
    from app.models.organization import Organization
    member = (
        db.query(OrganizationMember)
        .join(Organization)
        .filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == "OWNER",
            Organization.name.like("Personal Workspace%")
        )
        .first()
    )
    if member:
        return member.organization_id
    
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id, 
        OrganizationMember.role == "OWNER"
    ).first()
    return member.organization_id if member else None


def create_project(db: Session, project_in: ProjectCreate, owner_id: int) -> Project:
    default_org_id = _get_user_personal_workspace_id(db, owner_id)
    if not default_org_id:
        raise ValueError("User does not have a valid organization to create projects.")
    
    check_organization_permission(db, owner_id, default_org_id, ["OWNER", "ADMIN"])
    
    db_project = Project(**project_in.model_dump(), owner_id=owner_id, organization_id=default_org_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project_by_id(db: Session, project_id: int, owner_id: int) -> Optional[Project]:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id)
        )
        .first()
    )


def list_projects(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> List[Project]:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Project)
        .filter(or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id))
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_projects(db: Session, owner_id: int) -> int:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Project)
        .filter(or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id))
        .count()
    )


def update_project(
    db: Session, db_project: Project, project_in: ProjectUpdate, owner_id: int
) -> Project:
    check_project_action(db, db_project, owner_id, ["OWNER", "ADMIN"])
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, db_project: Project, owner_id: int) -> None:
    check_project_action(db, db_project, owner_id, ["OWNER", "ADMIN"])
    db.delete(db_project)
    db.commit()
