def test_create_project_no_auth(client):
    response = client.post(
        "/api/v1/projects/", json={"name": "Unauth Project", "description": "Will fail"}
    )
    assert response.status_code == 401


def test_create_project_auth(client, auth_token):
    response = client.post(
        "/api/v1/projects/",
        json={"name": "My Project", "description": "Auth Project"},
        headers=auth_token,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert data["owner_id"] is not None


def test_list_projects(client, auth_token):
    # Setup
    client.post("/api/v1/projects/", json={"name": "List Project"}, headers=auth_token)

    response = client.get("/api/v1/projects/", headers=auth_token)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) >= 1
    assert any(p["name"] == "List Project" for p in data["data"])

def test_cross_tenant_project_access_blocked(client, auth_token, auth_token_2):
    # User 1 cria um projeto
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "User 1 Project"},
        headers=auth_token,
    )
    project_id = resp.json()["id"]

    # User 2 tenta acessar o projeto do User 1
    resp2 = client.get(f"/api/v1/projects/{project_id}", headers=auth_token_2)
    assert resp2.status_code == 404
