import pytest

def test_delete_organization_with_invites(client, auth_token):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org to Delete"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "willbedeleted@example.com", "role": "MEMBER"},
        headers=auth_token
    )

    resp_del = client.delete(f"/api/v1/organizations/{org_id}", headers=auth_token)
    assert resp_del.status_code == 204
