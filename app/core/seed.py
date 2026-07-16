from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.tasks import create_task
from app.crud.users import authenticate_user, create_user, get_user_by_email
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate
from app.schemas.user import UserCreate


def seed_demo_data(db: Session) -> None:
    admin = get_user_by_email(db, settings.admin_email)
    if admin is None:
        admin = create_user(
            db,
            UserCreate(
                full_name="Platform Admin",
                email=settings.admin_email,
                password=settings.admin_password,
            ),
            role="admin",
        )

    demo_users = [
        ("Maya Johnson", "maya@example.com", "DemoPass123!"),
        ("Arjun Patel", "arjun@example.com", "DemoPass123!"),
    ]
    created_users = []
    for full_name, email, password in demo_users:
        user = get_user_by_email(db, email)
        if user is None:
            user = create_user(db, UserCreate(full_name=full_name, email=email, password=password))
        created_users.append(user)

    existing_titles = {"Launch landing page", "Review ECS deployment", "Harden authentication"}
    sample_tasks = [
        ("Launch landing page", "Finalize hero copy and CTA placement.", TaskStatus.IN_PROGRESS.value, TaskPriority.HIGH.value, date.today() + timedelta(days=2)),
        ("Review ECS deployment", "Verify task definition, ALB target group, and CloudWatch logs.", TaskStatus.TODO.value, TaskPriority.URGENT.value, date.today() + timedelta(days=1)),
        ("Harden authentication", "Check cookie flags, CSRF tokens, and password policy.", TaskStatus.DONE.value, TaskPriority.MEDIUM.value, date.today() - timedelta(days=3)),
    ]

    if created_users:
        user = created_users[0]
        for title, description, status, priority, due_date in sample_tasks:
            if title in existing_titles:
                continue
            task = TaskCreate(
                title=title,
                description=description,
                status=status,
                priority=priority,
                due_date=due_date,
            )
            create_task(db, user, task)

