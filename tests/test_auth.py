from __future__ import annotations


def test_register_login_and_dashboard(client):
    response = client.get("/register")
    assert response.status_code == 200
    csrf = client.cookies.get("csrf_token")
    assert csrf

    response = client.post(
        "/register",
        data={
            "csrf_token": csrf,
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Password123!",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert response.headers["location"].startswith("/dashboard")
    assert client.cookies.get("access_token")

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code in (302, 303)

    user_page = client.get("/dashboard/user")
    assert user_page.status_code == 200
    assert "User dashboard" in user_page.text

    logout_csrf = client.cookies.get("csrf_token")
    logout = client.post("/logout", data={"csrf_token": logout_csrf}, follow_redirects=False)
    assert logout.status_code in (302, 303)


def test_login_page_with_invalid_credentials_shows_error(client, admin_user):
    response = client.get("/login")
    assert response.status_code == 200
    csrf = client.cookies.get("csrf_token")
    response = client.post(
        "/login",
        data={"csrf_token": csrf, "email": "admin@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 400
    assert "Invalid email or password" in response.text

