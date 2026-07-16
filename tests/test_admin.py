from __future__ import annotations

from app.core.security import create_access_token, generate_csrf_token


def _set_admin_auth(client, admin_user):
    client.cookies.set("access_token", create_access_token(str(admin_user.id), admin_user.role))
    client.cookies.set("csrf_token", generate_csrf_token())


def test_admin_can_view_stats_and_users(client, admin_user, normal_user):
    _set_admin_auth(client, admin_user)

    stats = client.get("/api/v1/admin/stats")
    assert stats.status_code == 200
    assert "total" in stats.json()

    users = client.get("/api/v1/admin/users")
    assert users.status_code == 200
    assert len(users.json()) >= 2


def test_non_admin_cannot_access_admin_routes(client, normal_user):
    client.cookies.set("access_token", create_access_token(str(normal_user.id), normal_user.role))
    client.cookies.set("csrf_token", generate_csrf_token())
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 403

