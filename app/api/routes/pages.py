from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_current_user, validate_csrf
from app.core.security import clear_auth_cookies, create_access_token, generate_csrf_token, set_auth_cookies
from app.core.templates import render_template
from app.crud.tasks import create_task, delete_task, get_task, list_tasks, stats_for_admin, stats_for_user, update_task
from app.crud.users import authenticate_user, create_user, get_user_by_email, get_user_by_id, list_users, update_user_role
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate
from app.services.dashboard import overview_metrics, recent_audit_logs

router = APIRouter(tags=["pages"])


def _ensure_user(user: User | None) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def _redirect(url: str, message: str | None = None) -> RedirectResponse:
    target = f"{url}?notice={message}" if message else url
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)


def _set_login_cookies(response, access_token: str) -> None:
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, csrf_token)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), current_user=Depends(get_optional_current_user)):
    if current_user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render_template(
        request,
        "index.html",
        {
            "page_title": "Secure task management for modern teams",
            "show_hero": True,
        },
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user=Depends(get_optional_current_user)):
    if current_user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render_template(request, "auth_login.html", {"page_title": "Login"})


@router.post("/login")
async def login_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    email = str(form.get("email") or "").strip()
    password = str(form.get("password") or "")
    user = authenticate_user(db, email, password)
    if user is None:
        return render_template(
            request,
            "auth_login.html",
            {"page_title": "Login", "error": "Invalid email or password", "form_email": email},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = _redirect("/dashboard", "Welcome back")
    _set_login_cookies(response, create_access_token(str(user.id), user.role))
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, current_user=Depends(get_optional_current_user)):
    if current_user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render_template(request, "auth_register.html", {"page_title": "Create account"})


@router.post("/register")
async def register_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    payload_data = {
        "full_name": form.get("full_name"),
        "email": form.get("email"),
        "password": form.get("password"),
    }
    try:
        payload = UserCreate.model_validate(payload_data)
    except ValidationError as exc:
        return render_template(
            request,
            "auth_register.html",
            {"page_title": "Create account", "error": "Please fix the highlighted fields", "validation_errors": exc.errors(), "form": payload_data},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if get_user_by_email(db, payload.email):
        return render_template(
            request,
            "auth_register.html",
            {"page_title": "Create account", "error": "Email already registered", "form": payload_data},
            status_code=status.HTTP_409_CONFLICT,
        )
    user = create_user(db, payload, role="user")
    response = _redirect("/dashboard", "Account created")
    _set_login_cookies(response, create_access_token(str(user.id), user.role))
    return response


@router.post("/logout")
async def logout(request: Request, current_user=Depends(get_optional_current_user)):
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    response = _redirect("/", "You have been signed out")
    clear_auth_cookies(response)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role == "admin":
        return RedirectResponse("/dashboard/admin", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/dashboard/user", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard/user", response_class=HTMLResponse)
def user_dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    stats = stats_for_user(db, current_user)
    tasks = list_tasks(db, current_user)
    return render_template(
        request,
        "dashboard_user.html",
        {
            "page_title": "User dashboard",
            "user": current_user,
            "stats": stats,
            "tasks": tasks,
            "notice": request.query_params.get("notice"),
            "error": request.query_params.get("error"),
            "today": date.today(),
        },
    )


@router.get("/dashboard/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    metrics = overview_metrics(db)
    users = list_users(db)
    tasks = list_tasks(db, current_user)
    return render_template(
        request,
        "dashboard_admin.html",
        {
            "page_title": "Admin dashboard",
            "user": current_user,
            "metrics": metrics,
            "users": users,
            "tasks": tasks,
            "stats": stats_for_admin(db),
            "audit_logs": recent_audit_logs(db),
            "notice": request.query_params.get("notice"),
            "error": request.query_params.get("error"),
        },
    )


@router.get("/tasks/new", response_class=HTMLResponse)
def new_task_page(request: Request, current_user=Depends(get_current_user)):
    return render_template(request, "task_form.html", {"page_title": "New task", "mode": "create", "task": None, "user": current_user, "current_user": current_user})


@router.post("/tasks/new")
async def create_task_submit(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    payload_data = {
        "title": form.get("title"),
        "description": form.get("description"),
        "status": form.get("status") or "todo",
        "priority": form.get("priority") or "medium",
        "due_date": form.get("due_date") or None,
    }
    try:
        payload = TaskCreate.model_validate(payload_data)
    except ValidationError as exc:
        return render_template(
            request,
            "task_form.html",
            {"page_title": "New task", "mode": "create", "task": payload_data, "error": "Fix the fields below", "validation_errors": exc.errors(), "user": current_user, "current_user": current_user},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    create_task(db, current_user, payload)
    return _redirect("/dashboard/user", "Task created")


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def edit_task_page(task_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this task")
    return render_template(request, "task_form.html", {"page_title": "Edit task", "mode": "edit", "task": task, "user": current_user, "current_user": current_user})


@router.post("/tasks/{task_id}/edit")
async def edit_task_submit(task_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this task")
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    payload_data = {
        "title": form.get("title"),
        "description": form.get("description"),
        "status": form.get("status") or "todo",
        "priority": form.get("priority") or "medium",
        "due_date": form.get("due_date") or None,
    }
    try:
        payload = TaskUpdate.model_validate(payload_data)
    except ValidationError as exc:
        return render_template(
            request,
            "task_form.html",
            {"page_title": "Edit task", "mode": "edit", "task": task, "error": "Fix the fields below", "validation_errors": exc.errors(), "user": current_user, "current_user": current_user},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    update_task(db, task, payload)
    return _redirect("/dashboard/user" if current_user.role != "admin" else "/dashboard/admin", "Task updated")


@router.post("/tasks/{task_id}/delete")
async def delete_task_submit(task_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role != "admin" and task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this task")
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    delete_task(db, task)
    return _redirect("/dashboard/user" if current_user.role != "admin" else "/dashboard/admin", "Task deleted")


@router.post("/admin/users/{user_id}/role")
async def admin_role_update(user_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token") or ""))
    role = str(form.get("role") or "user")
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id and role != "admin":
        return _redirect("/dashboard/admin", "You cannot remove your own admin role")
    update_user_role(db, user, role)
    return _redirect("/dashboard/admin", "User role updated")
