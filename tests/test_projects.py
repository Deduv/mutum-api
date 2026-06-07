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
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "List Project"
