from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database import get_db
from app.models import User, Content, ArtRequest, Campaign, CalendarEvent
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/alertas", response_class=HTMLResponse)
async def alerts_page(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    alerts = build_alerts(db)
    return templates.TemplateResponse("alerts.html", {
        "request": request, "user": user, "page": "alertas",
        "alerts": alerts,
    })


@router.get("/api/alerts", tags=["alerts"])
async def get_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return build_alerts(db)


def build_alerts(db: Session):
    today = date.today()
    alerts = []

    overdue_contents = db.query(Content).filter(
        Content.due_date < today,
        Content.status.notin_(["finalizado", "postado"])
    ).all()
    for c in overdue_contents:
        days_late = (today - c.due_date).days
        alerts.append({
            "type": "danger",
            "icon": "exclamation-triangle",
            "category": "Conteudo Atrasado",
            "title": c.title,
            "message": f"{days_late} dia(s) de atraso - Status: {c.status}",
            "due_date": c.due_date.isoformat(),
            "link": "/conteudo",
        })

    overdue_arts = db.query(ArtRequest).filter(
        ArtRequest.deadline < today,
        ArtRequest.status != "aprovado"
    ).all()
    for a in overdue_arts:
        days_late = (today - a.deadline).days
        alerts.append({
            "type": "danger",
            "icon": "palette",
            "category": "Arte Nao Entregue",
            "title": a.title,
            "message": f"{days_late} dia(s) de atraso - Designer: {a.designer_name or 'N/A'}",
            "due_date": a.deadline.isoformat(),
            "link": "/artes",
        })

    upcoming_contents = db.query(Content).filter(
        Content.due_date >= today,
        Content.due_date <= today + timedelta(days=3),
        Content.status.notin_(["finalizado", "postado"])
    ).all()
    for c in upcoming_contents:
        days_left = (c.due_date - today).days
        alerts.append({
            "type": "warning",
            "icon": "clock",
            "category": "Prazo Proximo",
            "title": c.title,
            "message": f"Vence em {days_left} dia(s) - Status: {c.status}",
            "due_date": c.due_date.isoformat(),
            "link": "/conteudo",
        })

    upcoming_arts = db.query(ArtRequest).filter(
        ArtRequest.deadline >= today,
        ArtRequest.deadline <= today + timedelta(days=3),
        ArtRequest.status != "aprovado"
    ).all()
    for a in upcoming_arts:
        days_left = (a.deadline - today).days
        alerts.append({
            "type": "warning",
            "icon": "palette",
            "category": "Arte com Prazo Proximo",
            "title": a.title,
            "message": f"Vence em {days_left} dia(s) - Status: {a.status}",
            "due_date": a.deadline.isoformat(),
            "link": "/artes",
        })

    upcoming_campaigns = db.query(Campaign).filter(
        Campaign.start_date >= today,
        Campaign.start_date <= today + timedelta(days=7),
        Campaign.status == "planejamento"
    ).all()
    for camp in upcoming_campaigns:
        days_left = (camp.start_date - today).days
        alerts.append({
            "type": "info",
            "icon": "megaphone",
            "category": "Campanha Proxima",
            "title": camp.name,
            "message": f"Inicia em {days_left} dia(s)",
            "due_date": camp.start_date.isoformat(),
            "link": "/calendario",
        })

    upcoming_events = db.query(CalendarEvent).filter(
        CalendarEvent.date >= today,
        CalendarEvent.date <= today + timedelta(days=3),
        CalendarEvent.event_type == "data_importante"
    ).all()
    for ev in upcoming_events:
        days_left = (ev.date - today).days
        alerts.append({
            "type": "info",
            "icon": "calendar-event",
            "category": "Data Importante",
            "title": ev.title,
            "message": f"Em {days_left} dia(s)" if days_left > 0 else "HOJE!",
            "due_date": ev.date.isoformat(),
            "link": "/calendario",
        })

    alerts.sort(key=lambda x: (0 if x["type"] == "danger" else 1 if x["type"] == "warning" else 2, x.get("due_date", "")))
    return alerts
