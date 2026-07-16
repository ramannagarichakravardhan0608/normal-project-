from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.routes import admin_router, auth_router, pages_router, tasks_router
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.seed import seed_demo_data
from app.core.templates import render_template


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="TaskFlow Pro is a secure task management platform with dashboards, APIs, and AWS-ready deployment.",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)
app.state.settings = settings
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return render_template(
            request,
            "error.html",
            {
                "page_title": f"{exc.status_code} error",
                "status_code": exc.status_code,
                "title": "Request failed",
                "message": exc.detail,
            },
            status_code=exc.status_code,
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return render_template(request, "404.html", {"page_title": "Page not found"}, status_code=404)
    return JSONResponse({"detail": "Not Found"}, status_code=404)

