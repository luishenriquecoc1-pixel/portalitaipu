"""Helper to auto-create/update calendar events from other modules."""
from datetime import date
from sqlalchemy.orm import Session
from app.models import CalendarEvent
from app.date_utils import to_date

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


def auto_create_event(db: Session, title: str, event_date, source: str,
                      event_type: str = None, description: str = "",
                      content_id: int = None, campaign_id: int = None,
                      color: str = None, time: str = None):
    event_date = to_date(event_date) or date.today()

    ev = CalendarEvent(
        title=title,
        event_type=event_type or source,
        date=event_date,
        time=time,
        description=description,
        color=color or EVENT_COLORS.get(source, "#6366f1"),
        content_id=content_id,
        campaign_id=campaign_id,
        source=source,
    )
    db.add(ev)
    db.flush()
    return ev


def remove_auto_events(db: Session, source: str, content_id: int = None, campaign_id: int = None):
    query = db.query(CalendarEvent).filter(CalendarEvent.source == source)
    if content_id:
        query = query.filter(CalendarEvent.content_id == content_id)
    if campaign_id:
        query = query.filter(CalendarEvent.campaign_id == campaign_id)
    query.delete(synchronize_session=False)
