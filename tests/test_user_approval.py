def test_list_pending_users(client, auth_token, db_session):
    # Setup: Create a pending user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "pending@example.com", "password": "password123", "name": "Pending User"}
    )
    assert resp.status_code == 201
    
    # Authenticate as the active user (auth_token corresponds to the active test_user)
    resp = client.get("/api/v1/users/pending", headers=auth_token)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    
    # Check if pending user is in the list
    pending_user = next((u for u in data["data"] if u["email"] == "pending@example.com"), None)
    assert pending_user is not None
    assert pending_user["status"] == "PENDING"
    assert "password_hash" not in pending_user

def test_pending_user_cannot_access_list(client, db_session):
    # Setup: Create a pending user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "pending2@example.com", "password": "password123", "name": "Pending User 2"}
    )
    user_id = resp.json()["id"]
    
    # Forge token since login is blocked
    from app.core.security import create_access_token
    token = create_access_token(subject=user_id)
    
    # Try to access list
    resp = client.get("/api/v1/users/pending", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Inactive user"

def test_approve_pending_user(client, auth_token):
    # Setup: Create a pending user
    resp = client.post(
        "/api/v1/users/",
        json={"email": "pending3@example.com", "password": "password123", "name": "Pending User 3"}
    )
    user_id = resp.json()["id"]
    
    # Approve as active user
    resp = client.patch(f"/api/v1/users/{user_id}/approve", headers=auth_token)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACTIVE"
    assert "password_hash" not in data

def test_approve_nonexistent_user(client, auth_token):
    resp = client.patch("/api/v1/users/99999/approve", headers=auth_token)
    assert resp.status_code == 404

def test_approve_already_active_user(client, auth_token, test_user):
    # auth_token corresponds to test_user, who is already ACTIVE
    resp = client.patch(f"/api/v1/users/{test_user['id']}/approve", headers=auth_token)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"

