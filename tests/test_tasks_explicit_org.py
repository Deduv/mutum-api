def test_list_tasks_no_org_maintains_behavior(client, auth_token):
    resp = client.post(
        "/api/v1/projects/", json={"name": "Task Project"}, headers=auth_token
    )
    project_id = resp.json()["id"]

    # Create a task
    client.post(
        "/api/v1/tasks/",
        json={"title": "No Org Task", "project_id": project_id},
        headers=auth_token,
    )

    response = client.get("/api/v1/tasks/", headers=auth_token)
    assert response.status_code == 200
    data = response.json()
    assert any(t["title"] == "No Org Task" for t in data["data"])

def test_list_tasks_with_org_id_returns_only_org_tasks(client, auth_token, test_user):
    # Create an explicit organization
    org_resp = client.post("/api/v1/organizations/", json={"name": "Org 1"}, headers=auth_token)
    org1_id = org_resp.json()["id"]

    org2_resp = client.post("/api/v1/organizations/", json={"name": "Org 2"}, headers=auth_token)
    org2_id = org2_resp.json()["id"]

    # Create projects in those orgs
    p1_resp = client.post("/api/v1/projects/", json={"name": "P1", "organization_id": org1_id}, headers=auth_token)
    p1_id = p1_resp.json()["id"]

    p2_resp = client.post("/api/v1/projects/", json={"name": "P2", "organization_id": org2_id}, headers=auth_token)
    p2_id = p2_resp.json()["id"]

    # Create tasks
    client.post("/api/v1/tasks/", json={"title": "Task Org 1", "project_id": p1_id}, headers=auth_token)
    client.post("/api/v1/tasks/", json={"title": "Task Org 2", "project_id": p2_id}, headers=auth_token)

    # Fetch with org1
    resp1 = client.get(f"/api/v1/tasks/?organization_id={org1_id}", headers=auth_token)
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]
    assert len(data1) == 1
    assert data1[0]["title"] == "Task Org 1"

    # Fetch with org2
    resp2 = client.get(f"/api/v1/tasks/?organization_id={org2_id}", headers=auth_token)
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert len(data2) == 1
    assert data2[0]["title"] == "Task Org 2"

def test_user_outside_organization_blocked(client, auth_token_2, auth_token):
    # auth_token creates an org
    org_resp = client.post("/api/v1/organizations/", json={"name": "Org Secure"}, headers=auth_token)
    org_id = org_resp.json()["id"]

    # auth_token_2 tries to access
    resp = client.get(f"/api/v1/tasks/?organization_id={org_id}", headers=auth_token_2)
    assert resp.status_code == 403

def test_non_existent_organization(client, auth_token):
    resp = client.get("/api/v1/tasks/?organization_id=99999", headers=auth_token)
    assert resp.status_code == 404


def test_organization_id_zero(client, auth_token):
    resp = client.get("/api/v1/tasks/?organization_id=0", headers=auth_token)
    assert resp.status_code == 404

def test_legacy_owner_can_filter_by_org(client, auth_token, test_user, db_session):
    # Create an org and a project in it
    org_resp = client.post("/api/v1/organizations/", json={"name": "Legacy Org"}, headers=auth_token)
    org_id = org_resp.json()["id"]

    # auth_token is the creator of the org, so they are OWNER of the org.
    # To test legacy owner fallback, we need to remove the user from the organization members
    # but keep them as the Project.owner_id.
    
    p_resp = client.post("/api/v1/projects/", json={"name": "Legacy Project", "organization_id": org_id}, headers=auth_token)
    p_id = p_resp.json()["id"]
    
    # Create a task
    client.post("/api/v1/tasks/", json={"title": "Legacy Task", "project_id": p_id}, headers=auth_token)
    
    # Remove user from org members
    from app.models.organization_member import OrganizationMember
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == test_user["id"],
        OrganizationMember.organization_id == org_id
    ).first()
    if member:
        db_session.delete(member)
        db_session.commit()
        
    # Now user is NOT in org_ids. But they are the owner of the project.
    # When requesting /tasks/?organization_id=org_id, they should be able to see "Legacy Task"
    resp = client.get(f"/api/v1/tasks/?organization_id={org_id}", headers=auth_token)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "Legacy Task"

