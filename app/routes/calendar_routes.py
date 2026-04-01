from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import User, CalendarEvent, Campaign, Content
from app.auth import get_current_user
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

EVENT_TYPES = ["post", "campanha", "data_importante", "reuniao", "video", "arte", "conteudo"]
EVENT_COLORS = {
    "post": "#3b82f6",       # Azul
    "conteudo": "#3b82f6",   # Azul
    "video": "#8b5cf6",      # Roxo
    "arte": "#ec4899",       # Rosa
    "campanha": "#f59e0b",   # Laranja
    "reuniao": "#eab308",    # Amarelo
    "data_importante": "#ef4444",  # Vermelho
    "ideia": "#22c55e",      # Verde
    "copy": "#6366f1",       # Indigo
    "story": "#06b6d4",      # Cyan
    "reels": "#06b6d4",      # Cyan
}


@router.get("/calendario", response_class=HTMLResponse)
async def calendar_page(request: Request, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    campaigns = db.query(Campaign).all()
    contents = db.query(Content).all()
    return templates.TemplateResponse("calendar.html", {
        "request": request, "user": user, "page": "calendario",
        "event_types": EVENT_TYPES, "campaigns": campaigns, "contents": contents,
    })


@router.get("/api/calendar", tags=["calendar"])
async def list_events(month: int = None, year: int = None,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(CalendarEvent)
    if month and year:
        import calendar as cal
        first_day = date(year, month, 1)
        last_day = date(year, month, cal.monthrange(year, month)[1])
        query = query.filter(
            CalendarEvent.date >= first_day,
            CalendarEvent.date <= last_day,
        )
    items = query.order_by(CalendarEvent.date).all()
    return [{
        "id": e.id, "title": e.title, "event_type": e.event_type,
        "date": e.date.isoformat(),
        "time": e.time,
        "description": e.description,
        "color": e.color or EVENT_COLORS.get(e.event_type, "#6366f1"),
        "content_id": e.content_id, "campaign_id": e.campaign_id,
        "source": e.source if hasattr(e, 'source') else "manual",
    } for e in items]


@router.post("/api/calendar", tags=["calendar"])
async def create_event(request: Request, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    data = await request.json()
    event = CalendarEvent(
        title=data["title"],
        event_type=data.get("event_type", "post"),
        date=to_date(data["date"]),
        time=data.get("time") or None,
        description=data.get("description", ""),
        color=data.get("color", EVENT_COLORS.get(data.get("event_type", "post"), "#6366f1")),
        content_id=data.get("content_id"),
        campaign_id=data.get("campaign_id"),
        source="manual",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "title": event.title}


@router.put("/api/calendar/{event_id}", tags=["calendar"])
async def update_event(event_id: int, request: Request,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        return {"error": "Evento nao encontrado"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(event, key):
            if key == "date":
                val = to_date(val)
            setattr(event, key, val)
    db.commit()
    return {"ok": True}


@router.put("/api/calendar/{event_id}/move", tags=["calendar"])
async def move_event(event_id: int, request: Request,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Move event to a different date (drag and drop)."""
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        return {"error": "Evento nao encontrado"}
    data = await request.json()
    new_date = to_date(data.get("date"))
    if new_date:
        event.date = new_date
        db.commit()
        return {"ok": True, "new_date": event.date.isoformat()}
    return {"error": "Data invalida"}


@router.delete("/api/calendar/{event_id}", tags=["calendar"])
async def delete_event(event_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        return {"error": "Evento nao encontrado"}
    db.delete(event)
    db.commit()
    return {"ok": True}
