from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|blocked)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done|blocked)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None


class TaskRead(TaskBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class TaskWithOwner(TaskRead):
    owner_name: str
    owner_email: str


class TaskStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    blocked: int
    overdue: int

