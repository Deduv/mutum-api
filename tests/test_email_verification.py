from app.models.user import User
from app.core.security import generate_email_token


def test_register_creates_unverified_user(client, db_session):
    resp = client.post(
        "/api/v1/users/",
        json={"email": "newuser@example.com", "password": "password123", "name": "New User"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_email_verified"] is False
    assert data["status"] == "PENDING"

    # Query DB to make sure is_email_verified is False in database
    user = db_session.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.is_email_verified is False


def test_login_blocked_for_unverified_email(client, db_session):
    # Setup: Register user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "unverified@example.com", "password": "password123", "name": "Unverified User"}
    )
    assert resp.status_code == 201

    # Attempt login
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "unverified@example.com", "password": "password123"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Email not verified."


def test_verify_email_endpoint_success(client, db_session):
    # Setup: Register user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "toverify@example.com", "password": "password123", "name": "To Verify"}
    )
    assert resp.status_code == 201

    # Generate token
    token = generate_email_token("toverify@example.com")

    # Verify email
    resp = client.post(
        "/api/v1/auth/verify-email",
        json={"token": token}
    )
    assert resp.status_code == 200
    assert "verified successfully" in resp.json()["message"]

    # Verify state in DB
    user = db_session.query(User).filter(User.email == "toverify@example.com").first()
    assert user.is_email_verified is True
    # User is verified but still PENDING admin approval
    assert user.status == "PENDING"


def test_verify_email_invalid_token(client):
    resp = client.post(
        "/api/v1/auth/verify-email",
        json={"token": "invalidtoken123"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid or expired token"


def test_resend_verification_email(client, db_session):
    # Setup: Register user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "resend@example.com", "password": "password123", "name": "Resend"}
    )
    assert resp.status_code == 201

    # Request resend
    resp = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "resend@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Verification email resent"


def test_resend_verification_already_verified(client, db_session):
    # Setup: Register user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "alreadyverified@example.com", "password": "password123", "name": "Already"}
    )
    assert resp.status_code == 201

    # Verify email first
    token = generate_email_token("alreadyverified@example.com")
    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    # Request resend (should return 400 because email is already verified)
    resp = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "alreadyverified@example.com"}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already verified"


def test_sequential_approval_flow(client, db_session, super_admin_token):
    # 1. Register user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "seq@example.com", "password": "password123", "name": "Sequential"}
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # 2. Check pending list (should NOT be there because email is not verified yet)
    resp = client.get("/api/v1/users/pending", headers=super_admin_token)
    assert resp.status_code == 200
    pending_emails = [u["email"] for u in resp.json()["data"]]
    assert "seq@example.com" not in pending_emails

    # 3. Verify email
    token = generate_email_token("seq@example.com")
    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    # 4. Check pending list again (should now be visible to admin)
    resp = client.get("/api/v1/users/pending", headers=super_admin_token)
    assert resp.status_code == 200
    pending_emails = [u["email"] for u in resp.json()["data"]]
    assert "seq@example.com" in pending_emails

    # 5. Admin approves user
    resp = client.patch(f"/api/v1/users/{user_id}/approve", headers=super_admin_token)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"

    # 6. Login succeeds now
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "seq@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
