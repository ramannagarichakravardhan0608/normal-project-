from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, generate_csrf_token, set_auth_cookies
from app.crud.users import authenticate_user, create_user, get_user_by_email
from app.schemas.auth import AuthResponse, LoginRequest
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def auth_payload(user) -> AuthResponse:
    return AuthResponse(access_token="", user=UserRead.model_validate(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = create_user(db, payload, role="user")
    access_token = create_access_token(str(user.id), user.role)
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, csrf_token)
    return AuthResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    access_token = create_access_token(str(user.id), user.role)
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, csrf_token)
    return AuthResponse(access_token=access_token, user=UserRead.model_validate(user))


@router.post("/logout")
def logout(response: Response, current_user=Depends(get_current_user)):
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")
    return response


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    return UserRead.model_validate(current_user)
