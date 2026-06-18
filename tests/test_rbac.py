import pytest
from app.models.organization_member import OrganizationMember
from app.models.project import Project

def _change_user_role(db_session, user_id, project_id, role):
    project = db_session.query(Project).filter(Project.id == project_id).first()
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == project.organization_id
    ).first()
    if not member:
        member = OrganizationMember(
            user_id=user_id, 
            organization_id=project.organization_id, 
            role=role
        )
        db_session.add(member)
    else:
        member.role = role
    db_session.commit()

def test_rbac_project_deletion_and_patch(client, auth_token, auth_token_2, test_user_2, db_session):
    # 1. OWNER creates project
    resp = client.post("/api/v1/projects/", json={"name": "RBAC Project"}, headers=auth_token)
    project_id = resp.json()["id"]

    # 2. Add user 2 as MEMBER
    _change_user_role(db_session, test_user_2["id"], project_id, "MEMBER")
    
    # 3. MEMBER tries to update project (should fail)
    resp_patch_member = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated by MEMBER"}, headers=auth_token_2)
    assert resp_patch_member.status_code == 403

    # 4. MEMBER tries to delete project (should fail)
    resp_del_member = client.delete(f"/api/v1/projects/{project_id}", headers=auth_token_2)
    assert resp_del_member.status_code == 403

    # 5. Change user 2 to ADMIN
    _change_user_role(db_session, test_user_2["id"], project_id, "ADMIN")
    
    # 6. ADMIN tries to update project (should succeed)
    resp_patch_admin = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated by ADMIN"}, headers=auth_token_2)
    assert resp_patch_admin.status_code == 200
    
    # 7. ADMIN tries to delete project (should succeed)
    resp_del_admin = client.delete(f"/api/v1/projects/{project_id}", headers=auth_token_2)
    assert resp_del_admin.status_code == 204

    # 8. OWNER can delete project
    resp2 = client.post("/api/v1/projects/", json={"name": "RBAC Project 2"}, headers=auth_token)
    project2_id = resp2.json()["id"]
    resp_patch_owner = client.patch(f"/api/v1/projects/{project2_id}", json={"name": "Updated by OWNER"}, headers=auth_token)
    assert resp_patch_owner.status_code == 200
    resp_del_owner = client.delete(f"/api/v1/projects/{project2_id}", headers=auth_token)
    assert resp_del_owner.status_code == 204

def test_rbac_task_actions(client, auth_token, auth_token_2, test_user_2, db_session):
    # 1. OWNER creates project and task
    resp = client.post("/api/v1/projects/", json={"name": "RBAC Task Project"}, headers=auth_token)
    project_id = resp.json()["id"]
    
    resp_t = client.post("/api/v1/tasks/", json={"title": "RBAC Task", "project_id": project_id}, headers=auth_token)
    task_id = resp_t.json()["id"]

    # Try to access task as User 2 (not in org)
    resp_no_access = client.get(f"/api/v1/tasks/{task_id}", headers=auth_token_2)
    assert resp_no_access.status_code == 404

    # 2. Add user 2 as MEMBER
    _change_user_role(db_session, test_user_2["id"], project_id, "MEMBER")
    
    # 3. MEMBER tries to create a task (should succeed)
    resp_create = client.post("/api/v1/tasks/", json={"title": "MEMBER Task", "project_id": project_id}, headers=auth_token_2)
    assert resp_create.status_code == 201
    
    # 4. MEMBER tries to update a task (should succeed)
    resp_update = client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Updated by MEMBER"}, headers=auth_token_2)
    assert resp_update.status_code == 200

    # 5. MEMBER tries to delete task (should fail)
    resp_del_member = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_token_2)
    assert resp_del_member.status_code == 403
    
    # 6. Change user 2 to ADMIN
    _change_user_role(db_session, test_user_2["id"], project_id, "ADMIN")
    
    # 7. ADMIN tries to delete task (should succeed)
    resp_del_admin = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_token_2)
    assert resp_del_admin.status_code == 204

    # 8. OWNER can delete task
    resp_t2 = client.post("/api/v1/tasks/", json={"title": "RBAC Task 2", "project_id": project_id}, headers=auth_token)
    task2_id = resp_t2.json()["id"]
    resp_del_owner = client.delete(f"/api/v1/tasks/{task2_id}", headers=auth_token)
    assert resp_del_owner.status_code == 204

def test_rbac_demoted_owner_id(client, auth_token, test_user, db_session):
    # Test owner_id demoted to MEMBER
    resp = client.post("/api/v1/projects/", json={"name": "Demoted Owner Project"}, headers=auth_token)
    project_id = resp.json()["id"]

    resp_t = client.post("/api/v1/tasks/", json={"title": "Demoted Task", "project_id": project_id}, headers=auth_token)
    task_id = resp_t.json()["id"]

    # Demote original owner to MEMBER
    _change_user_role(db_session, test_user["id"], project_id, "MEMBER")

    # Demoted owner should NOT be able to delete or patch project
    resp_patch = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Patch by demoted"}, headers=auth_token)
    assert resp_patch.status_code == 403

    resp_del = client.delete(f"/api/v1/projects/{project_id}", headers=auth_token)
    assert resp_del.status_code == 403

    # Demoted owner should NOT be able to delete task
    resp_del_task = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_token)
    assert resp_del_task.status_code == 403

def test_rbac_fallback_owner_id(client, auth_token, test_user, db_session):
    # Test legacy owner_id fallback logic where no membership exists
    resp = client.post("/api/v1/projects/", json={"name": "Fallback Project"}, headers=auth_token)
    project_id = resp.json()["id"]

    # manually delete the organization member record
    project = db_session.query(Project).filter(Project.id == project_id).first()
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == test_user["id"],
        OrganizationMember.organization_id == project.organization_id
    ).first()
    db_session.delete(member)
    db_session.commit()

    # Even without OrganizationMember, the original owner_id should act as OWNER
    resp_patch = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated legacy"}, headers=auth_token)
    assert resp_patch.status_code == 200

    resp_del_fallback = client.delete(f"/api/v1/projects/{project_id}", headers=auth_token)
    assert resp_del_fallback.status_code == 204
