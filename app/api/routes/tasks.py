from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.crud.tasks import create_task, delete_task, get_task, list_tasks, update_task
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _task_to_schema(task: Task) -> TaskRead:
    return TaskRead.model_validate(task)


def _authorize_task(user: User, task: Task) -> None:
    if user.role != "admin" and task.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this task")


@router.get("", response_model=list[TaskRead])
def get_tasks(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return [_task_to_schema(task) for task in list_tasks(db, current_user)]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_new_task(payload: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = create_task(db, current_user, payload)
    return _task_to_schema(task)


@router.get("/{task_id}", response_model=TaskRead)
def read_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(current_user, task)
    return _task_to_schema(task)


@router.put("/{task_id}", response_model=TaskRead)
def edit_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(current_user, task)
    return _task_to_schema(update_task(db, task, payload))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _authorize_task(current_user, task)
    delete_task(db, task)
    return None

