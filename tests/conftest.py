import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.db.base import Base
from app.models.user import User

# Usa SQLite in-memory para testes em ambiente 100% isolado
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # Cria as tabelas do zero a cada teste para garantir isolamento
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Reseta o banco no fim do teste
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Fechamento da session é garantido pelo fixture db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client, db_session):
    user_data = {
        "name": "Test User",
        "email": "test@pytest.com",
        "password": "testpassword",
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    user_data["id"] = response.json()["id"]
    
    # Ativa o usuário no banco para permitir o login na suíte de testes
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    user.status = "ACTIVE"
    db_session.commit()
    
    return user_data


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_user_2(client, db_session):
    user_data = {
        "name": "Test User 2",
        "email": "test2@pytest.com",
        "password": "testpassword2",
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    user_data["id"] = response.json()["id"]
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    user.status = "ACTIVE"
    db_session.commit()
    return user_data

@pytest.fixture(scope="function")
def auth_token_2(client, test_user_2):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user_2["email"], "password": test_user_2["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def super_admin_user(client, db_session):
    user_data = {
        "name": "Super Admin",
        "email": "admin@pytest.com",
        "password": "adminpassword",
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    user_data["id"] = response.json()["id"]
    user = db_session.query(User).filter(User.email == user_data["email"]).first()
    user.status = "ACTIVE"
    user.is_super_admin = True
    db_session.commit()
    return user_data


@pytest.fixture(scope="function")
def super_admin_token(client, super_admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": super_admin_user["email"],
            "password": super_admin_user["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
