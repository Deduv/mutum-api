import pytest


@pytest.fixture
def project_id(client, auth_token):
    resp = client.post(
        "/api/v1/projects/", json={"name": "Task Project"}, headers=auth_token
    )
    return resp.json()["id"]


def test_create_task_no_auth(client, project_id):
    response = client.post(
        "/api/v1/tasks/", json={"title": "Unauth Task", "project_id": project_id}
    )
    assert response.status_code == 401


def test_create_task_auth(client, auth_token, project_id):
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Auth Task", "project_id": project_id},
        headers=auth_token,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Auth Task"
    assert data["status"] == "TODO"
    assert data["priority"] == "MEDIUM"


def test_update_task(client, auth_token, project_id):
    resp = client.post(
        "/api/v1/tasks/",
        json={"title": "Task to update", "project_id": project_id},
        headers=auth_token,
    )
    task_id = resp.json()["id"]

    update_resp = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "DONE", "priority": "HIGH"},
        headers=auth_token,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "DONE"
    assert update_resp.json()["priority"] == "HIGH"


def test_list_tasks(client, auth_token, project_id):
    client.post(
        "/api/v1/tasks/",
        json={"title": "List Task", "project_id": project_id},
        headers=auth_token,
    )

    response = client.get("/api/v1/tasks/", headers=auth_token)
    assert response.status_code == 200
    assert "data" in response.json()
    assert len(response.json()["data"]) >= 1
    assert any(t["title"] == "List Task" for t in response.json()["data"])

def test_cross_tenant_task_assignment_blocked(client, auth_token, test_user_2, project_id):
    # test_user_2 ID
    user2_id = test_user_2["id"]
    
    # Try to assign task to test_user_2 who is NOT in the organization of auth_token user's project
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Cross Tenant Task", "project_id": project_id, "assigned_user_id": user2_id},
        headers=auth_token,
    )
    assert response.status_code == 400
    assert "belong to the project's organization" in response.json()["detail"]
