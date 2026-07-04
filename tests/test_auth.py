from app.models.user import User

def test_create_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "name": "Auth Test User",
            "email": "authtest@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "authtest@example.com"
    assert "id" in response.json()
    assert "password_hash" not in response.json()


def test_login_success(client, db_session):
    client.post(
        "/api/v1/users/",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "password",
        },
    )
    
    user = db_session.query(User).filter(User.email == "login@example.com").first()
    user.status = "ACTIVE"
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_users_me(client, auth_token):
    response = client.get("/api/v1/users/me", headers=auth_token)
    assert response.status_code == 200
    assert response.json()["email"] == "test@pytest.com"
