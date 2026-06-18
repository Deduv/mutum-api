from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import organization_service, organization_invite_service
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
    OrganizationMemberResponse,
    OrganizationMemberListResponse
)
from app.schemas.organization_invite import (
    OrganizationInviteCreate,
    OrganizationInviteResponse,
    OrganizationInviteListResponse
)

router = APIRouter()

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_service.create_organization(db, org_in=org_in, user_id=current_user.id)


@router.get("/", response_model=OrganizationListResponse)
def read_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orgs = organization_service.list_organizations(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    total = organization_service.count_organizations(db, user_id=current_user.id)
    return OrganizationListResponse(data=orgs, total=total, skip=skip, limit=limit)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def read_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = organization_service.get_organization(
        db, organization_id=organization_id, user_id=current_user.id
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: int,
    org_in: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_service.update_organization(
        db, organization_id=organization_id, org_in=org_in, user_id=current_user.id
    )

@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_service.delete_organization(
        db, organization_id=organization_id, user_id=current_user.id
    )
    return None

@router.get("/{organization_id}/members", response_model=OrganizationMemberListResponse)
def read_organization_members(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    members = organization_service.list_members(
        db, organization_id=organization_id, user_id=current_user.id
    )
    return OrganizationMemberListResponse(data=members, total=len(members))

@router.post("/{organization_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
def add_organization_member(
    organization_id: int,
    member_in: OrganizationMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_service.add_member(
        db, organization_id=organization_id, member_in=member_in, user_id=current_user.id
    )

@router.patch("/{organization_id}/members/{user_id}", response_model=OrganizationMemberResponse)
def update_organization_member(
    organization_id: int,
    user_id: int,
    member_in: OrganizationMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_service.update_member_role(
        db, organization_id=organization_id, target_user_id=user_id, member_in=member_in, user_id=current_user.id
    )

@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_member(
    organization_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_service.remove_member(
        db, organization_id=organization_id, target_user_id=user_id, user_id=current_user.id
    )
    return None

@router.post("/{organization_id}/invites", response_model=OrganizationInviteResponse, status_code=status.HTTP_201_CREATED)
def create_organization_invite(
    organization_id: int,
    invite_in: OrganizationInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_invite_service.create_invite(
        db, organization_id=organization_id, invite_in=invite_in, user_id=current_user.id
    )

@router.get("/{organization_id}/invites", response_model=OrganizationInviteListResponse)
def list_organization_invites(
    organization_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return organization_invite_service.list_invites(
        db, organization_id=organization_id, user_id=current_user.id, skip=skip, limit=limit
    )

@router.delete("/{organization_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_organization_invite(
    organization_id: int,
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_invite_service.revoke_invite(
        db, organization_id=organization_id, invite_id=invite_id, user_id=current_user.id
    )
    return None

@router.post("/invites/{token}/accept", status_code=status.HTTP_200_OK)
def accept_organization_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    organization_invite_service.accept_invite(
        db, token=token, user_id=current_user.id
    )
    return {"status": "accepted"}
