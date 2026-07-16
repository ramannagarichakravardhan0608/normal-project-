from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.core.config import settings
from app.core.deps import get_csrf_token
from app.core.security import CSRF_COOKIE_NAME

templates = Jinja2Templates(directory="app/templates")


def render_template(request: Request, template_name: str, context: dict | None = None, status_code: int = 200) -> Response:
    context = context or {}
    csrf_token = get_csrf_token(request)
    context.update(
        {
            "request": request,
            "app_name": settings.app_name,
            "csrf_token": csrf_token,
        }
    )
    response = templates.TemplateResponse(request=request, name=template_name, context=context, status_code=status_code)
    if request.cookies.get(CSRF_COOKIE_NAME) != csrf_token:
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,
            secure=settings.secure_cookies,
            samesite="lax",
            path="/",
        )
    return response
