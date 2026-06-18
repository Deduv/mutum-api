from app.models.organization_member import OrganizationMember
from app.models.project import Project

def test_create_organization(client, auth_token, db_session, test_user):
    resp = client.post("/api/v1/organizations/", json={"name": "New Org"}, headers=auth_token)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Org"
    org_id = data["id"]
    
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == test_user["id"],
        OrganizationMember.organization_id == org_id
    ).first()
    assert member.role == "OWNER"

def test_list_organizations(client, auth_token):
    client.post("/api/v1/organizations/", json={"name": "Org 1"}, headers=auth_token)
    
    resp = client.get("/api/v1/organizations/", headers=auth_token)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
    assert any(o["name"] == "Org 1" for o in data["data"])

def test_external_user_cannot_access(client, auth_token, auth_token_2):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Private"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    resp_view = client.get(f"/api/v1/organizations/{org_id}", headers=auth_token_2)
    assert resp_view.status_code == 404
    
def test_organization_member_management(client, auth_token, auth_token_2, test_user, test_user_2):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Management Org"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    # 1. OWNER adiciona membro (MEMBER)
    resp_add = client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": test_user_2["id"], "role": "MEMBER"},
        headers=auth_token
    )
    assert resp_add.status_code == 201

    # 2. MEMBER acessa detalhes da propria org
    resp_get = client.get(f"/api/v1/organizations/{org_id}", headers=auth_token_2)
    assert resp_get.status_code == 200
    
    # 3. MEMBER não adiciona membro
    user_data = {"name": "Test User temp", "email": "temp@pytest.com", "password": "pw"}
    user_id = client.post("/api/v1/users/", json=user_data).json()["id"]
    resp_add_member = client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": user_id, "role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_add_member.status_code == 403

    # 4. OWNER altera role para ADMIN
    resp_patch = client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user_2['id']}", 
        json={"role": "ADMIN"},
        headers=auth_token
    )
    assert resp_patch.status_code == 200

    # 5. ADMIN não rebaixa OWNER
    resp_patch_admin = client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user['id']}", 
        json={"role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_patch_admin.status_code == 403

    # 6. ADMIN não remove OWNER
    resp_del_admin = client.delete(
        f"/api/v1/organizations/{org_id}/members/{test_user['id']}", 
        headers=auth_token_2
    )
    assert resp_del_admin.status_code == 403

def test_admin_add_and_remove(client, auth_token, auth_token_2, test_user_2):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org 2"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": test_user_2["id"], "role": "ADMIN"},
        headers=auth_token
    )

    user_data = {"name": "Test User 3", "email": "test3@pytest.com", "password": "pw"}
    resp = client.post("/api/v1/users/", json=user_data)
    user3_id = resp.json()["id"]

    # ADMIN adiciona membro
    resp_add = client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": user3_id, "role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_add.status_code == 201

    # remoção de membro funciona
    resp_del = client.delete(
        f"/api/v1/organizations/{org_id}/members/{user3_id}", 
        headers=auth_token_2
    )
    assert resp_del.status_code == 204

def test_cannot_remove_last_owner(client, auth_token, test_user):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org 3"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    resp_del = client.delete(f"/api/v1/organizations/{org_id}/members/{test_user['id']}", headers=auth_token)
    assert resp_del.status_code == 400
    assert "Cannot remove the last OWNER" in resp_del.json()["detail"]

def test_cannot_demote_last_owner(client, auth_token, test_user):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Demote"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    resp_patch = client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user['id']}", 
        json={"role": "ADMIN"},
        headers=auth_token
    )
    assert resp_patch.status_code == 400
    assert "Cannot demote the last OWNER" in resp_patch.json()["detail"]

def test_can_demote_owner_if_multiple(client, auth_token, test_user_2, test_user):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Multi Owner"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    # Add second owner
    resp_add = client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": test_user_2["id"], "role": "OWNER"},
        headers=auth_token
    )
    assert resp_add.status_code == 201

    # Now demote the original owner
    resp_patch = client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user['id']}", 
        json={"role": "ADMIN"},
        headers=auth_token
    )
    assert resp_patch.status_code == 200

def test_add_member_missing_user(client, auth_token):
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Missing"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    resp_add = client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": 99999, "role": "MEMBER"},
        headers=auth_token
    )
    assert resp_add.status_code == 404
    assert "User not found" in resp_add.json()["detail"]

def test_update_organization(client, auth_token, auth_token_2, test_user_2):
    # Create org (OWNER)
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Update"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    # 1. OWNER atualiza organização
    resp_patch = client.patch(f"/api/v1/organizations/{org_id}", json={"name": "Org Updated by OWNER"}, headers=auth_token)
    assert resp_patch.status_code == 200
    assert resp_patch.json()["name"] == "Org Updated by OWNER"

    # Add User 2 as MEMBER
    client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": test_user_2["id"], "role": "MEMBER"},
        headers=auth_token
    )

    # 2. MEMBER não atualiza organização
    resp_patch_member = client.patch(f"/api/v1/organizations/{org_id}", json={"name": "Hacked"}, headers=auth_token_2)
    assert resp_patch_member.status_code == 403

    # Promote User 2 to ADMIN
    client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user_2['id']}", 
        json={"role": "ADMIN"},
        headers=auth_token
    )

    # 3. ADMIN atualiza organização
    resp_patch_admin = client.patch(f"/api/v1/organizations/{org_id}", json={"name": "Org Updated by ADMIN"}, headers=auth_token_2)
    assert resp_patch_admin.status_code == 200
    assert resp_patch_admin.json()["name"] == "Org Updated by ADMIN"

    # 4. usuário externo não atualiza organização
    # We can just create a new org and try to update it with auth_token_2
    resp_create_2 = client.post("/api/v1/organizations/", json={"name": "Org Update 2"}, headers=auth_token)
    org_id_2 = resp_create_2.json()["id"]
    
    resp_patch_ext = client.patch(f"/api/v1/organizations/{org_id_2}", json={"name": "Hacked Ext"}, headers=auth_token_2)
    assert resp_patch_ext.status_code == 404

def test_delete_organization(client, auth_token, auth_token_2, test_user_2, db_session):
    # Create org
    resp_create = client.post("/api/v1/organizations/", json={"name": "Org Delete"}, headers=auth_token)
    org_id = resp_create.json()["id"]

    # Add User 2 as ADMIN
    client.post(
        f"/api/v1/organizations/{org_id}/members", 
        json={"user_id": test_user_2["id"], "role": "ADMIN"},
        headers=auth_token
    )

    # 1. ADMIN não deleta organização
    resp_del_admin = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token_2)
    assert resp_del_admin.status_code == 403

    # Demote User 2 to MEMBER
    client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user_2['id']}", 
        json={"role": "MEMBER"},
        headers=auth_token
    )

    # 2. MEMBER não deleta organização
    resp_del_member = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token_2)
    assert resp_del_member.status_code == 403

    # 3. usuário externo não deleta organização
    resp_create_2 = client.post("/api/v1/organizations/", json={"name": "Org Delete 2"}, headers=auth_token)
    org_id_2 = resp_create_2.json()["id"]
    
    resp_del_ext = client.delete(f"/api/v1/organizations/{org_id_2}", headers=auth_token_2)
    assert resp_del_ext.status_code == 404

    # 4. não permitir deletar organização com membros extras
    resp_del_owner = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token)
    assert resp_del_owner.status_code == 400
    assert "Cannot delete organization with extra members" in resp_del_owner.json()["detail"]

    # Remove the extra member
    client.delete(f"/api/v1/organizations/{org_id}/members/{test_user_2['id']}", headers=auth_token)

    project = Project(name="Proj", organization_id=org_id, owner_id=test_user_2["id"])
    db_session.add(project)
    db_session.commit()

    # 5. não permitir deletar organização com projetos
    resp_del_owner_proj = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token)
    assert resp_del_owner_proj.status_code == 400
    assert "Cannot delete organization with existing projects" in resp_del_owner_proj.json()["detail"]

    # Delete project
    db_session.delete(project)
    db_session.commit()

    # 6. OWNER deleta organização vazia
    resp_del_final = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token)
    assert resp_del_final.status_code == 204
