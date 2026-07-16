from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.crud.tasks import stats_for_admin
from app.crud.users import get_user_by_id, list_users, update_user_role
from app.schemas.task import TaskStats
from app.schemas.user import UserPublic, UserRoleUpdate

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats", response_model=TaskStats)
def stats(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return TaskStats(**stats_for_admin(db))


@router.get("/users", response_model=list[UserPublic])
def users(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return [UserPublic.model_validate(user) for user in list_users(db)]


@router.patch("/users/{user_id}", response_model=UserPublic)
def change_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id and payload.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own admin role")
    return UserPublic.model_validate(update_user_role(db, user, payload.role))

