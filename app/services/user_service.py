from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole


def create_user(db: Session, user_in: UserCreate) -> User:
    try:
        db_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
        )
        db.add(db_user)
        db.flush()

        org_name = f"Personal Workspace - {db_user.name}" if db_user.name else f"Personal Workspace - User {db_user.id}"
        db_org = Organization(name=org_name)
        db.add(db_org)
        db.flush()

        db_member = OrganizationMember(
            user_id=db_user.id,
            organization_id=db_org.id,
            role=OrganizationRole.OWNER
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise e


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    normalized_email = email.strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def count_users(db: Session) -> int:
    return db.query(User).count()

def get_pending_users(db: Session) -> List[User]:
    return db.query(User).filter(User.status == "PENDING").all()

def approve_user(db: Session, user: User) -> User:
    if user.status != "ACTIVE":
        user.status = "ACTIVE"
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
