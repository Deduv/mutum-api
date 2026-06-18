from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.models.user import User
from app.services import task_service

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.create_task(db, task_in=task_in, owner_id=current_user.id)


@router.get("/", response_model=TaskListResponse)
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = task_service.list_tasks(
        db, owner_id=current_user.id, skip=skip, limit=limit
    )
    total = task_service.count_tasks(db, owner_id=current_user.id)
    return TaskListResponse(data=tasks, total=total, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.get_task_by_id(db, task_id=task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=404, detail="Task not found or you don't have access"
        )
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.get_task_by_id(db, task_id=task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=404, detail="Task not found or you don't have access"
        )
    return task_service.update_task(
        db, db_task=task, task_in=task_in, owner_id=current_user.id
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = task_service.get_task_by_id(db, task_id=task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=404, detail="Task not found or you don't have access"
        )
    task_service.delete_task(db, db_task=task, owner_id=current_user.id)
    return None
