import pytest
from app.models.user import User
from app.schemas.user import UserCreate
from app.services import user_service
from app.models.organization_invite import InviteStatus
from app.services import organization_invite_service
from app.schemas.organization_invite import OrganizationInviteCreate

def test_user_creation_normalizes_email(db_session):
    user_in = UserCreate(email=" Mixed.Case@EXAMPLE.com ", password="password123")
    user = user_service.create_user(db_session, user_in=user_in)
    
    # Assert it was saved normalized
    assert user.email == "mixed.case@example.com"

def test_user_creation_duplicate_case_insensitive(db_session):
    user_in_1 = UserCreate(email="duplicate@example.com", password="password123")
    user_service.create_user(db_session, user_in=user_in_1)
    
    # Second creation with different case should fail DB unique constraint or Pydantic validation (actually DB will fail)
    user_in_2 = UserCreate(email=" DUPLICATE@ExAmPlE.com ", password="password456")
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        user_service.create_user(db_session, user_in=user_in_2)

def test_user_login_with_different_case(client, db_session):
    # Setup user
    from app.models.user import UserStatus
    user_in = UserCreate(email="user@example.com", password="password123")
    user = user_service.create_user(db_session, user_in=user_in)
    user.status = UserStatus.ACTIVE
    db_session.add(user)
    db_session.commit()
    
    # Login with mixed case should work since we normalize on lookup
    response = client.post(
        "/api/v1/auth/login",
        data={"username": " UsEr@ExamplE.com ", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_invite_acceptance_with_different_case(client, auth_token, test_user_2, db_session):
    # Setup org with test_user
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Invite Normalize"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    # test_user_2 has email test2@pytest.com
    # Invite is created with a different case
    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": " TEST2@PYTEST.COM ", "role": "MEMBER"},
        headers=auth_token
    )
    assert resp_inv.status_code == 201
    invite_token = resp_inv.json()["token"]

    # Let's generate a token for test2@pytest.com
    resp_login = client.post(
        "/api/v1/auth/login",
        data={"username": "test2@pytest.com", "password": "testpassword2"}
    )
    auth_token_2 = {"Authorization": f"Bearer {resp_login.json()['access_token']}"}

    resp_accept = client.post(f"/api/v1/organizations/invites/{invite_token}/accept", headers=auth_token_2)
    assert resp_accept.status_code == 200
    assert resp_accept.json()["status"] == "accepted"
