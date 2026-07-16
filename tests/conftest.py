from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AUTO_SEED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "Admin@12345")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import create_access_token, generate_csrf_token  # noqa: E402
from app.crud.users import create_user  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402


@pytest.fixture(autouse=True)
def prepare_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_user(db_session):
    user = create_user(
        db_session,
        UserCreate(full_name="Admin User", email="admin@example.com", password="Admin@12345"),
        role=UserRole.ADMIN.value,
    )
    return user


@pytest.fixture()
def normal_user(db_session):
    user = create_user(
        db_session,
        UserCreate(full_name="Normal User", email="user@example.com", password="Password123!"),
        role=UserRole.USER.value,
    )
    return user


@pytest.fixture()
def auth_headers(admin_user):
    token = create_access_token(str(admin_user.id), admin_user.role)
    csrf = generate_csrf_token()
    return {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf}
