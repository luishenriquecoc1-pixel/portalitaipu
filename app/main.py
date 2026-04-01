import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.auth import NotAuthenticatedException
from app.routes import (
    auth_routes, dashboard_routes, content_routes, video_routes,
    art_routes, copy_routes, calendar_routes, ideas_routes,
    alerts_routes, metrics_routes,
    search_routes, checklist_routes, comment_routes, attachment_routes,
    label_routes, rule_routes, template_routes, inspiration_routes,
    tv_routes, timeline_routes,
)

app = FastAPI(title="Portal MKT - Gestao de Marketing", version="2.0.0")

os.makedirs("app/static/uploads/arts", exist_ok=True)
os.makedirs("app/static/uploads/attachments", exist_ok=True)

# Auto-create tables and seed admin on startup
from app.database import engine, Base
from app.models import *
from app.seed import seed_admin
Base.metadata.create_all(bind=engine)
seed_admin()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Core routes
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(content_routes.router)
app.include_router(video_routes.router)
app.include_router(art_routes.router)
app.include_router(copy_routes.router)
app.include_router(calendar_routes.router)
app.include_router(ideas_routes.router)
app.include_router(alerts_routes.router)
app.include_router(metrics_routes.router)

# New feature routes
app.include_router(search_routes.router)
app.include_router(checklist_routes.router)
app.include_router(comment_routes.router)
app.include_router(attachment_routes.router)
app.include_router(label_routes.router)
app.include_router(rule_routes.router)
app.include_router(template_routes.router)
app.include_router(inspiration_routes.router)
app.include_router(tv_routes.router)
app.include_router(timeline_routes.router)


@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Nao autenticado"})
    return RedirectResponse(url="/login", status_code=302)
