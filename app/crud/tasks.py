from datetime import datetime, timezone

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


def task_query_for_user(user: User):
    statement = select(Task).order_by(Task.created_at.desc())
    if user.role != "admin":
        statement = statement.where(Task.owner_id == user.id)
    return statement


def list_tasks(db: Session, user: User) -> list[Task]:
    return list(db.scalars(task_query_for_user(user)))


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def create_task(db: Session, user: User, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        owner_id=user.id,
    )
    if task.status == TaskStatus.DONE.value:
        task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    if payload.title is not None:
        task.title = payload.title.strip()
    if payload.description is not None:
        task.description = payload.description.strip()
    if payload.status is not None:
        task.status = payload.status
        task.completed_at = datetime.now(timezone.utc) if payload.status == TaskStatus.DONE.value else None
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.due_date is not None:
        task.due_date = payload.due_date
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def stats_for_user(db: Session, user: User) -> dict[str, int]:
    base = select(Task).where(Task.owner_id == user.id)
    return {
        "total": db.scalar(select(func.count()).select_from(base.subquery())) or 0,
        "todo": db.scalar(select(func.count(Task.id)).where(and_(Task.owner_id == user.id, Task.status == TaskStatus.TODO.value))) or 0,
        "in_progress": db.scalar(
            select(func.count(Task.id)).where(and_(Task.owner_id == user.id, Task.status == TaskStatus.IN_PROGRESS.value))
        )
        or 0,
        "done": db.scalar(select(func.count(Task.id)).where(and_(Task.owner_id == user.id, Task.status == TaskStatus.DONE.value))) or 0,
        "blocked": db.scalar(
            select(func.count(Task.id)).where(and_(Task.owner_id == user.id, Task.status == TaskStatus.BLOCKED.value))
        )
        or 0,
        "overdue": db.scalar(
            select(func.count(Task.id)).where(and_(Task.owner_id == user.id, Task.due_date.is_not(None), Task.due_date < func.current_date(), Task.status != TaskStatus.DONE.value))
        )
        or 0,
    }


def stats_for_admin(db: Session) -> dict[str, int]:
    return {
        "total": db.scalar(select(func.count(Task.id))) or 0,
        "todo": db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatus.TODO.value)) or 0,
        "in_progress": db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatus.IN_PROGRESS.value)) or 0,
        "done": db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatus.DONE.value)) or 0,
        "blocked": db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatus.BLOCKED.value)) or 0,
        "overdue": db.scalar(
            select(func.count(Task.id)).where(Task.due_date.is_not(None), Task.due_date < func.current_date(), Task.status != TaskStatus.DONE.value)
        )
        or 0,
    }

