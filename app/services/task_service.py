from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from fastapi import HTTPException, status
from sqlalchemy import or_
from app.models.organization_member import OrganizationMember

def _get_user_organization_ids(db: Session, user_id: int) -> list[int]:
    members = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).all()
    return [m.organization_id for m in members]

def _check_user_in_organization(db: Session, user_id: int, organization_id: int):
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user does not belong to the project's organization",
        )


def _check_project_ownership(db: Session, project_id: int, owner_id: int) -> Project:
    org_ids = _get_user_organization_ids(db, owner_id)
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id)
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you don't have access",
        )
    return project


def _check_user_exists(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user does not exist",
        )
    return user


def create_task(db: Session, task_in: TaskCreate, owner_id: int) -> Task:
    project = _check_project_ownership(db, task_in.project_id, owner_id)
    if task_in.assigned_user_id:
        _check_user_exists(db, task_in.assigned_user_id)
        _check_user_in_organization(db, task_in.assigned_user_id, project.organization_id)

    db_task = Task(**task_in.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task_by_id(db: Session, task_id: int, owner_id: int) -> Optional[Task]:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Task)
        .join(Project)
        .filter(
            Task.id == task_id,
            or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id)
        )
        .first()
    )


def list_tasks(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> List[Task]:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Task)
        .join(Project)
        .filter(or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id))
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_tasks(db: Session, owner_id: int) -> int:
    org_ids = _get_user_organization_ids(db, owner_id)
    return (
        db.query(Task)
        .join(Project)
        .filter(or_(Project.organization_id.in_(org_ids), Project.owner_id == owner_id))
        .count()
    )


def update_task(db: Session, db_task: Task, task_in: TaskUpdate, owner_id: int) -> Task:
    if task_in.assigned_user_id:
        _check_user_exists(db, task_in.assigned_user_id)
        _check_user_in_organization(db, task_in.assigned_user_id, db_task.project.organization_id)

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: Task) -> None:
    db.delete(db_task)
    db.commit()
