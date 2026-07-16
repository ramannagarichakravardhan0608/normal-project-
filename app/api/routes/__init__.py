from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.pages import router as pages_router
from app.api.routes.tasks import router as tasks_router

__all__ = ["admin_router", "auth_router", "pages_router", "tasks_router"]

