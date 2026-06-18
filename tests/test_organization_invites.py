import pytest
from datetime import datetime, timedelta, timezone
from app.models.organization_member import OrganizationMember
from app.models.organization_invite import OrganizationInvite, InviteStatus

def test_owner_create_invite(client, auth_token, test_user):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org 1"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "newuser@example.com", "role": "MEMBER"},
        headers=auth_token
    )
    assert resp_inv.status_code == 201
    assert resp_inv.json()["email"] == "newuser@example.com"
    assert resp_inv.json()["status"] == "PENDING"
    assert "token" in resp_inv.json()

def test_admin_create_invite(client, auth_token, auth_token_2, test_user_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Admin"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": test_user_2["id"], "role": "ADMIN"},
        headers=auth_token
    )

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "newuser2@example.com", "role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_inv.status_code == 201

def test_member_cannot_create_invite(client, auth_token, auth_token_2, test_user_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Member"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": test_user_2["id"], "role": "MEMBER"},
        headers=auth_token
    )

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "newuser3@example.com", "role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_inv.status_code == 403

def test_external_cannot_create_invite(client, auth_token, auth_token_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Ext"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "newuser4@example.com", "role": "MEMBER"},
        headers=auth_token_2
    )
    assert resp_inv.status_code == 404

def test_owner_list_invites(client, auth_token):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org List"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "u1@example.com", "role": "MEMBER"}, headers=auth_token)
    client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "u2@example.com", "role": "MEMBER"}, headers=auth_token)

    resp_list = client.get(f"/api/v1/organizations/{org_id}/invites", headers=auth_token)
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] == 2

def test_member_cannot_list_invites(client, auth_token, auth_token_2, test_user_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org List Mem"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": test_user_2["id"], "role": "MEMBER"}, headers=auth_token)

    resp_list = client.get(f"/api/v1/organizations/{org_id}/invites", headers=auth_token_2)
    assert resp_list.status_code == 403

def test_owner_revoke_invite(client, auth_token, auth_token_2, test_user_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Revoke"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "rev@example.com", "role": "MEMBER"}, headers=auth_token)
    invite_id = resp_inv.json()["id"]

    client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": test_user_2["id"], "role": "MEMBER"}, headers=auth_token)

    # Member cannot revoke
    resp_rev_mem = client.delete(f"/api/v1/organizations/{org_id}/invites/{invite_id}", headers=auth_token_2)
    assert resp_rev_mem.status_code == 403

    # Owner revokes
    resp_rev_owner = client.delete(f"/api/v1/organizations/{org_id}/invites/{invite_id}", headers=auth_token)
    assert resp_rev_owner.status_code == 204

def test_accept_invite_success(client, auth_token, auth_token_2, test_user_2, db_session):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Accept"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": test_user_2["email"], "role": "ADMIN"}, headers=auth_token)
    token = resp_inv.json()["token"]

    resp_accept = client.post(f"/api/v1/organizations/invites/{token}/accept", headers=auth_token_2)
    assert resp_accept.status_code == 200

    member = db_session.query(OrganizationMember).filter(OrganizationMember.user_id == test_user_2["id"], OrganizationMember.organization_id == org_id).first()
    assert member is not None
    assert member.role == "ADMIN"

    # Cannot reuse
    resp_accept_2 = client.post(f"/api/v1/organizations/invites/{token}/accept", headers=auth_token_2)
    assert resp_accept_2.status_code == 400
    assert "already been accepted" in resp_accept_2.json()["detail"]

def test_accept_invite_wrong_email(client, auth_token, auth_token_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Wrong Acc"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "other@pytest.com", "role": "MEMBER"}, headers=auth_token)
    token = resp_inv.json()["token"]

    resp_accept = client.post(f"/api/v1/organizations/invites/{token}/accept", headers=auth_token_2)
    assert resp_accept.status_code == 403
    assert "does not match user email" in resp_accept.json()["detail"]

def test_expired_invite(client, auth_token, auth_token_2, test_user_2, db_session):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Exp"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": test_user_2["email"], "role": "MEMBER"}, headers=auth_token)
    token = resp_inv.json()["token"]

    # manually expire
    invite = db_session.query(OrganizationInvite).filter(OrganizationInvite.token == token).first()
    invite.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    resp_accept = client.post(f"/api/v1/organizations/invites/{token}/accept", headers=auth_token_2)
    assert resp_accept.status_code == 400
    assert "expired" in resp_accept.json()["detail"]

def test_duplicate_pending_invite_blocked(client, auth_token):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Dup"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv_1 = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "dup@example.com", "role": "MEMBER"}, headers=auth_token)
    assert resp_inv_1.status_code == 201

    resp_inv_2 = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "dup@example.com", "role": "MEMBER"}, headers=auth_token)
    assert resp_inv_2.status_code == 400
    assert "pending invite already exists" in resp_inv_2.json()["detail"]

def test_admin_cannot_invite_owner(client, auth_token, auth_token_2, test_user_2):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Admin Invite Owner"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": test_user_2["id"], "role": "ADMIN"},
        headers=auth_token
    )

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "newowner@example.com", "role": "OWNER"},
        headers=auth_token_2
    )
    assert resp_inv.status_code == 403
    assert "ADMIN cannot invite an OWNER" in resp_inv.json()["detail"]

def test_invalid_email_invite(client, auth_token):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Invalid Email"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": "invalid-email", "role": "MEMBER"},
        headers=auth_token
    )
    assert resp_inv.status_code == 422
    assert "Invalid email format" in str(resp_inv.json())

def test_duplicate_invite_different_case(client, auth_token):
    resp_org = client.post("/api/v1/organizations/", json={"name": "Org Dup Case"}, headers=auth_token)
    org_id = resp_org.json()["id"]

    resp_inv_1 = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "DupCase@example.com", "role": "MEMBER"}, headers=auth_token)
    assert resp_inv_1.status_code == 201

    resp_inv_2 = client.post(f"/api/v1/organizations/{org_id}/invites", json={"email": "dupcase@EXAMPLE.com", "role": "MEMBER"}, headers=auth_token)
    assert resp_inv_2.status_code == 400
    assert "pending invite already exists" in resp_inv_2.json()["detail"]
