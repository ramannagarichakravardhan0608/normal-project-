from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.task import Task
from app.models.user import User


def recent_audit_logs(db: Session, limit: int = 10) -> list[AuditLog]:
    statement: Select[tuple[AuditLog]] = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.scalars(statement))


def overview_metrics(db: Session) -> dict[str, int]:
    return {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "tasks": db.scalar(select(func.count(Task.id))) or 0,
        "admins": db.scalar(select(func.count(User.id)).where(User.role == "admin")) or 0,
        "active_users": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
    }

