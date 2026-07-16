from __future__ import annotations

from app.core.security import create_access_token, generate_csrf_token
from app.crud.users import create_user
from app.schemas.user import UserCreate
from app.crud.tasks import create_task
from app.schemas.task import TaskCreate


def _set_auth(client, user):
    token = create_access_token(str(user.id), user.role)
    client.cookies.set("access_token", token)
    client.cookies.set("csrf_token", generate_csrf_token())


def test_user_can_create_list_update_delete_task(client, normal_user, db_session):
    _set_auth(client, normal_user)

    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Write docs",
            "description": "Document the deployment workflow",
            "status": "todo",
            "priority": "high",
            "due_date": "2026-07-20",
        },
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "done", "priority": "urgent"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "done"

    delete_response = client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == 204


def test_ownership_rules_prevent_cross_user_task_access(client, normal_user, admin_user, db_session):
    task = create_task(
        db_session,
        normal_user,
        TaskCreate(title="Private task", description="Owner only", status="todo", priority="medium", due_date=None),
    )

    other_user = create_user(
        db_session,
        UserCreate(full_name="Another User", email="another@example.com", password="Password123!"),
    )
    _set_auth(client, other_user)
    forbidden = client.get(f"/api/v1/tasks/{task.id}")
    assert forbidden.status_code == 403
