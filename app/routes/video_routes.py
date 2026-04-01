from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Video, Content
from app.auth import get_current_user
from app.calendar_helper import auto_create_event, remove_auto_events
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

VIDEO_STATUSES = ["roteiro", "gravado", "edicao", "finalizado"]


@router.get("/videos", response_class=HTMLResponse)
async def videos_page(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True).all()
    contents = db.query(Content).filter(Content.content_type == "video").all()
    return templates.TemplateResponse("videos.html", {
        "request": request, "user": user, "page": "videos",
        "users": users, "contents": contents, "statuses": VIDEO_STATUSES,
    })


@router.get("/api/videos", tags=["videos"])
async def list_videos(status: str = None, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    query = db.query(Video)
    if status:
        query = query.filter(Video.status == status)
    items = query.order_by(Video.updated_at.desc()).all()
    return [{
        "id": v.id, "title": v.title, "script": v.script,
        "location": v.location, "status": v.status,
        "content_id": v.content_id, "responsible_id": v.responsible_id,
        "responsible_name": v.responsible.full_name if v.responsible else None,
        "due_date": v.due_date.isoformat() if v.due_date else None,
        "notes": v.notes, "duration_seconds": v.duration_seconds,
        "created_at": v.created_at.isoformat(),
    } for v in items]


@router.post("/api/videos", tags=["videos"])
async def create_video(request: Request, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    data = await request.json()
    video = Video(
        title=data["title"],
        script=data.get("script", ""),
        location=data.get("location", ""),
        status=data.get("status", "roteiro"),
        content_id=data.get("content_id"),
        responsible_id=data.get("responsible_id"),
        due_date=to_date(data.get("due_date")),
        notes=data.get("notes", ""),
        duration_seconds=data.get("duration_seconds"),
    )
    db.add(video)
    db.flush()

    if video.due_date:
        auto_create_event(db, f"[Video] {video.title}",
                          video.due_date, source="video",
                          event_type="video",
                          description=f"Local: {video.location or 'N/A'} | Status: {video.status}")
    db.commit()
    db.refresh(video)
    return {"id": video.id, "title": video.title}


@router.put("/api/videos/{video_id}", tags=["videos"])
async def update_video(video_id: int, request: Request,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return {"error": "Video nao encontrado"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(video, key):
            setattr(video, key, val)
    db.commit()
    return {"ok": True}


@router.delete("/api/videos/{video_id}", tags=["videos"])
async def delete_video(video_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return {"error": "Video nao encontrado"}
    db.delete(video)
    db.commit()
    return {"ok": True}
