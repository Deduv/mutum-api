"""Tests for super_admin authorization on user management endpoints (SEC-1).

Covers:
- Regular ACTIVE user gets 403 on admin-only routes
- Super admin gets 200 on admin-only routes
- GET /users/me returns is_super_admin correctly
- GET /users/ requires authentication
"""


# --- Negative cases: regular ACTIVE user is denied ---


def test_regular_user_cannot_list_pending(client, auth_token):
    """ACTIVE user without is_super_admin gets 403 on GET /users/pending."""
    resp = client.get("/api/v1/users/pending", headers=auth_token)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not enough permissions"


def test_regular_user_cannot_approve(client, auth_token):
    """ACTIVE user without is_super_admin gets 403 on PATCH /users/{id}/approve."""
    # Create a pending user to try to approve
    resp = client.post(
        "/api/v1/users/",
        json={
            "email": "target@example.com",
            "password": "password123",
            "name": "Target User",
        },
    )
    user_id = resp.json()["id"]

    resp = client.patch(f"/api/v1/users/{user_id}/approve", headers=auth_token)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not enough permissions"


def test_regular_user_cannot_list_users(client, auth_token):
    """ACTIVE user without is_super_admin gets 403 on GET /users/."""
    resp = client.get("/api/v1/users/", headers=auth_token)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not enough permissions"


def test_regular_user_cannot_get_user_by_id(client, auth_token, test_user):
    """ACTIVE user without is_super_admin gets 403 on GET /users/{id}."""
    resp = client.get(f"/api/v1/users/{test_user['id']}", headers=auth_token)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not enough permissions"


# --- Positive cases: super admin is allowed ---


def test_super_admin_can_list_pending(client, super_admin_token):
    """Super admin can list pending users."""
    resp = client.get("/api/v1/users/pending", headers=super_admin_token)
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_super_admin_can_approve(client, super_admin_token, db_session):
    """Super admin can approve a pending user."""
    resp = client.post(
        "/api/v1/users/",
        json={
            "email": "pending_sa@example.com",
            "password": "password123",
            "name": "Pending SA",
        },
    )
    user_id = resp.json()["id"]

    # Verify email
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "pending_sa@example.com").first()
    user.is_email_verified = True
    db_session.commit()

    resp = client.patch(
        f"/api/v1/users/{user_id}/approve", headers=super_admin_token
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"


def test_super_admin_can_list_users(client, super_admin_token):
    """Super admin can list all users."""
    resp = client.get("/api/v1/users/", headers=super_admin_token)
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_super_admin_can_get_user_by_id(client, super_admin_token, test_user):
    """Super admin can get a user by ID."""
    resp = client.get(
        f"/api/v1/users/{test_user['id']}", headers=super_admin_token
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == test_user["id"]


# --- /me endpoint returns is_super_admin ---


def test_me_returns_is_super_admin_false(client, auth_token):
    """/me returns is_super_admin=false for regular user."""
    resp = client.get("/api/v1/users/me", headers=auth_token)
    assert resp.status_code == 200
    assert resp.json()["is_super_admin"] is False


def test_me_returns_is_super_admin_true(client, super_admin_token):
    """/me returns is_super_admin=true for super admin."""
    resp = client.get("/api/v1/users/me", headers=super_admin_token)
    assert resp.status_code == 200
    assert resp.json()["is_super_admin"] is True


# --- Authentication required (401 without token) ---


def test_list_users_requires_auth(client):
    """GET /users/ without token returns 401."""
    resp = client.get("/api/v1/users/")
    assert resp.status_code == 401


def test_get_user_by_id_requires_auth(client):
    """GET /users/{id} without token returns 401."""
    resp = client.get("/api/v1/users/1")
    assert resp.status_code == 401


def test_list_pending_requires_auth(client):
    """GET /users/pending without token returns 401."""
    resp = client.get("/api/v1/users/pending")
    assert resp.status_code == 401


def test_approve_requires_auth(client):
    """PATCH /users/{id}/approve without token returns 401."""
    resp = client.patch("/api/v1/users/1/approve")
    assert resp.status_code == 401
