from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_in: ProjectCreate, owner_id: int) -> Project:
    db_project = Project(**project_in.model_dump(), owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project_by_id(db: Session, project_id: int, owner_id: int) -> Optional[Project]:
    return (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == owner_id)
        .first()
    )


def list_projects(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_projects(db: Session, owner_id: int) -> int:
    return db.query(Project).filter(Project.owner_id == owner_id).count()


def update_project(
    db: Session, db_project: Project, project_in: ProjectUpdate
) -> Project:
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, db_project: Project) -> None:
    db.delete(db_project)
    db.commit()
