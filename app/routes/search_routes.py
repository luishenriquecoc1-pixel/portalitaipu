from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Content, Video, ArtRequest, Idea, Campaign, CalendarEvent

router = APIRouter()


@router.get("/api/search", tags=["search"])
async def global_search(q: str = "", db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    if not q or len(q.strip()) < 2:
        return {"contents": [], "videos": [], "arts": [], "ideas": [],
                "campaigns": [], "events": []}

    term = q.strip()

    contents = db.query(Content).filter(
        (Content.title.contains(term)) | (Content.description.contains(term))
    ).all()

    videos = db.query(Video).filter(Video.title.contains(term)).all()

    arts = db.query(ArtRequest).filter(ArtRequest.title.contains(term)).all()

    ideas = db.query(Idea).filter(
        (Idea.title.contains(term)) | (Idea.description.contains(term))
    ).all()

    campaigns = db.query(Campaign).filter(Campaign.name.contains(term)).all()

    events = db.query(CalendarEvent).filter(CalendarEvent.title.contains(term)).all()

    return {
        "contents": [{
            "id": c.id, "title": c.title, "description": c.description,
            "content_type": c.content_type, "status": c.status,
        } for c in contents],
        "videos": [{
            "id": v.id, "title": v.title, "status": v.status,
            "content_id": v.content_id,
        } for v in videos],
        "arts": [{
            "id": a.id, "title": a.title, "status": a.status,
            "content_id": a.content_id,
        } for a in arts],
        "ideas": [{
            "id": i.id, "title": i.title, "description": i.description,
            "is_converted": i.is_converted,
        } for i in ideas],
        "campaigns": [{
            "id": c.id, "name": c.name, "status": c.status,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
        } for c in campaigns],
        "events": [{
            "id": e.id, "title": e.title, "event_type": e.event_type,
            "date": e.date.isoformat() if e.date else None,
        } for e in events],
    }
