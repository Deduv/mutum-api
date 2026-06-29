from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import BackgroundTasks
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, generate_email_token
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.core.email import send_email
from app.core.config import settings


def create_user(db: Session, user_in: UserCreate, background_tasks: Optional[BackgroundTasks] = None) -> User:
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

        # Enviar e-mail de verificação
        token = generate_email_token(db_user.email)
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Verifique seu e-mail - Mutum"
        html_content = (
            f"<p>Olá {db_user.name or 'Usuário'},</p>"
            f"<p>Obrigado por se cadastrar no Mutum. "
            f"Clique no link abaixo para verificar seu endereço de e-mail:</p>"
            f"<p><a href='{verification_link}'>{verification_link}</a></p>"
            f"<p>Este link expira em 24 horas.</p>"
        )

        if background_tasks:
            background_tasks.add_task(send_email, db_user.email, subject, html_content)
        else:
            send_email(db_user.email, subject, html_content)

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
    # Retorna apenas os usuários pendentes de aprovação e com e-mail verificado
    return db.query(User).filter(User.status == "PENDING", User.is_email_verified).all()


def verify_user_email(db: Session, user: User, background_tasks: BackgroundTasks) -> User:
    """Marca o e-mail do usuário como verificado e notifica os super admins por e-mail."""
    user.is_email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)

    # Buscar todos os super admins ativos
    super_admins = db.query(User).filter(User.is_super_admin, User.status == "ACTIVE").all()
    for admin in super_admins:
        admin_link = f"{settings.FRONTEND_URL}/admin/users"
        subject = "[Mutum] Novo usuário aguardando aprovação"
        html_content = (
            f"<p>Olá {admin.name or 'Administrador'},</p>"
            f"<p>O usuário <strong>{user.name}</strong> ({user.email}) confirmou o e-mail "
            f"e está aguardando sua aprovação para acessar a plataforma.</p>"
            f"<p>Você pode aprovar a conta no link: "
            f"<a href='{admin_link}'>{admin_link}</a></p>"
        )
        if background_tasks:
            background_tasks.add_task(send_email, admin.email, subject, html_content)
        else:
            send_email(admin.email, subject, html_content)

    return user


def approve_user(db: Session, user: User) -> User:
    if user.status != "ACTIVE":
        user.status = "ACTIVE"
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

