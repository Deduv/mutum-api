from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_super_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserListResponse
from app.services import user_service

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user.
    """
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = user_service.create_user(db, user_in=user_in)
    return user


@router.get("/", response_model=UserListResponse)
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """
    Retrieve users. Requires super admin.
    """
    users = user_service.list_users(db, skip=skip, limit=limit)
    total = user_service.count_users(db)
    return UserListResponse(data=users, total=total, skip=skip, limit=limit)


@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user

@router.get("/pending", response_model=UserListResponse)
def read_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """
    Retrieve pending users. Requires super admin.
    """
    users = user_service.get_pending_users(db)
    return UserListResponse(data=users, total=len(users), skip=0, limit=len(users))

@router.patch("/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """
    Approve a pending user. Requires super admin.
    """
    user = user_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user_service.approve_user(db, user=user)


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """
    Get a specific user by id. Requires super admin.
    """
    user = user_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

