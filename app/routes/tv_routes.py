from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Content, CalendarEvent, Campaign, ArtRequest, Video

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/tv", response_class=HTMLResponse)
async def tv_page(request: Request, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    today = date.today()

    # Contents in production (status producao or aprovacao)
    contents_production = db.query(Content).filter(
        Content.status.in_(["producao", "aprovacao"])
    ).order_by(Content.updated_at.desc()).all()

    # Today's calendar events
    today_events = db.query(CalendarEvent).filter(
        CalendarEvent.date == today
    ).order_by(CalendarEvent.time).all()

    # Overdue items (due_date before today, not finished)
    overdue_count = db.query(Content).filter(
        Content.due_date < today,
        Content.status.notin_(["finalizado", "postado"])
    ).count()

    # Active campaigns
    active_campaigns = db.query(Campaign).filter(
        Campaign.status.notin_(["finalizado", "cancelado"]),
        Campaign.end_date >= today,
    ).all()

    # Pending art requests
    pending_arts = db.query(ArtRequest).filter(
        ArtRequest.status.notin_(["aprovado", "cancelado"])
    ).order_by(ArtRequest.deadline).all()

    # Pending videos
    pending_videos = db.query(Video).filter(
        Video.status.notin_(["finalizado", "cancelado"])
    ).order_by(Video.due_date).all()

    return templates.TemplateResponse("tv.html", {
        "request": request,
        "user": user,
        "contents_production": [{
            "id": c.id, "title": c.title, "content_type": c.content_type,
            "status": c.status, "priority": c.priority,
            "responsible_name": c.responsible.full_name if c.responsible else None,
            "due_date": c.due_date.isoformat() if c.due_date else None,
        } for c in contents_production],
        "today_events": [{
            "id": e.id, "title": e.title, "event_type": e.event_type,
            "time": e.time, "color": e.color,
        } for e in today_events],
        "overdue_count": overdue_count,
        "active_campaigns": [{
            "id": c.id, "name": c.name, "color": c.color,
            "status": c.status,
            "end_date": c.end_date.isoformat() if c.end_date else None,
        } for c in active_campaigns],
        "pending_arts": [{
            "id": a.id, "title": a.title, "status": a.status,
            "deadline": a.deadline.isoformat() if a.deadline else None,
        } for a in pending_arts],
        "pending_videos": [{
            "id": v.id, "title": v.title, "status": v.status,
            "due_date": v.due_date.isoformat() if v.due_date else None,
        } for v in pending_videos],
    })
