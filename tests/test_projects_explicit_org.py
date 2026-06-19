def test_create_project_explicit_org_owner(client, auth_token):
    # Setup organization
    resp_org = client.post("/api/v1/organizations/", json={"name": "Explicit Org"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    # Create project passing org_id
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Explicit Project", "organization_id": org_id},
        headers=auth_token,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Explicit Project"
    assert resp.json()["organization_id"] == org_id

def test_create_project_explicit_org_admin(client, auth_token, auth_token_2, test_user_2):
    # User 1 creates org
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Admin"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    # User 1 adds User 2 as ADMIN
    client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": test_user_2["id"], "role": "ADMIN"}, headers=auth_token)

    # User 2 tries to create project
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Explicit Project Admin", "organization_id": org_id},
        headers=auth_token_2,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Explicit Project Admin"
    assert resp.json()["organization_id"] == org_id

def test_create_project_explicit_org_member_denied(client, auth_token, auth_token_2, test_user_2):
    # User 1 creates org
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org 2"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    # User 1 adds User 2 as MEMBER
    client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": test_user_2["id"], "role": "MEMBER"}, headers=auth_token)

    # User 2 tries to create project
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Explicit Project Member", "organization_id": org_id},
        headers=auth_token_2,
    )
    assert resp.status_code == 403

def test_create_project_explicit_org_external_denied(client, auth_token, auth_token_2):
    # User 1 creates org
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org 3"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    # User 2 tries to create project (not a member)
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Explicit Project External", "organization_id": org_id},
        headers=auth_token_2,
    )
    assert resp.status_code == 403

def test_create_project_invalid_org(client, auth_token):
    resp = client.post(
        "/api/v1/projects/",
        json={"name": "Explicit Project Invalid Org", "organization_id": 99999},
        headers=auth_token,
    )
    assert resp.status_code == 404

def test_list_projects_explicit_org(client, auth_token, auth_token_2):
    # Create two orgs and a project in each
    resp_org1 = client.post("/api/v1/organizations/", json={"name": "List Org 1"}, headers=auth_token)
    org1_id = resp_org1.json()["id"]
    client.post("/api/v1/projects/", json={"name": "Project Org 1", "organization_id": org1_id}, headers=auth_token)

    resp_org2 = client.post("/api/v1/organizations/", json={"name": "List Org 2"}, headers=auth_token)
    org2_id = resp_org2.json()["id"]
    client.post("/api/v1/projects/", json={"name": "Project Org 2", "organization_id": org2_id}, headers=auth_token)

    # List projects for Org 1
    resp = client.get(f"/api/v1/projects/?organization_id={org1_id}", headers=auth_token)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Project Org 1"
    assert data[0]["organization_id"] == org1_id

    # External user lists projects for Org 1
    resp_ext = client.get(f"/api/v1/projects/?organization_id={org1_id}", headers=auth_token_2)
    assert resp_ext.status_code == 403
