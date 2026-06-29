from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db
from app.core.security import verify_password, create_access_token, generate_email_token, verify_email_token
from app.services import user_service
from app.schemas.token import Token
from app.models.user import UserStatus
from app.core.email import send_email
from app.core.config import settings

router = APIRouter()


class EmailVerificationTokenSchema(BaseModel):
    token: str


class ResendVerificationSchema(BaseModel):
    email: str


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = user_service.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified.",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval.",
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(
    token_data: EmailVerificationTokenSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify a user's email using the signed token.
    """
    email = verify_email_token(token_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    user = user_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_email_verified:
        return {"message": "Email already verified"}

    user_service.verify_user_email(db, user=user, background_tasks=background_tasks)
    return {"message": "Email verified successfully. Pending admin approval."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(
    request_data: ResendVerificationSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend email verification token to a user.
    """
    user = user_service.get_user_by_email(db, email=request_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    token = generate_email_token(user.email)
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verifique seu e-mail - Mutum"
    html_content = (
        f"<p>Olá {user.name or 'Usuário'},</p>"
        f"<p>Clique no link abaixo para verificar seu endereço de e-mail:</p>"
        f"<p><a href='{verification_link}'>{verification_link}</a></p>"
        f"<p>Este link expira em 24 horas.</p>"
    )

    background_tasks.add_task(send_email, user.email, subject, html_content)
    return {"message": "Verification email resent"}

