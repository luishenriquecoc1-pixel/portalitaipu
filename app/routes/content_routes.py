from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Content, Campaign
from app.auth import get_current_user
from app.calendar_helper import auto_create_event, remove_auto_events
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

STATUSES = ["ideia", "producao", "aprovacao", "finalizado", "postado"]
TYPES = ["video", "story", "spot", "campanha", "post", "reels"]
PRIORITIES = ["baixa", "media", "alta", "urgente"]


@router.get("/conteudo", response_class=HTMLResponse)
async def content_page(request: Request, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True).all()
    campaigns = db.query(Campaign).all()
    return templates.TemplateResponse("content.html", {
        "request": request, "user": user, "page": "conteudo",
        "users": users, "campaigns": campaigns,
        "statuses": STATUSES, "types": TYPES, "priorities": PRIORITIES,
    })


@router.get("/api/contents", tags=["contents"])
async def list_contents(status: str = None, content_type: str = None,
                        db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Content)
    if status:
        query = query.filter(Content.status == status)
    if content_type:
        query = query.filter(Content.content_type == content_type)
    items = query.order_by(Content.column_order, Content.updated_at.desc()).all()

    return [{
        "id": c.id, "title": c.title, "description": c.description,
        "content_type": c.content_type, "status": c.status,
        "responsible_id": c.responsible_id,
        "responsible_name": c.responsible.full_name if c.responsible else None,
        "campaign_id": c.campaign_id,
        "campaign_name": c.campaign.name if c.campaign else None,
        "due_date": c.due_date.isoformat() if c.due_date else None,
        "priority": c.priority, "column_order": c.column_order,
        "is_favorite": c.is_favorite,
        "is_recurring": c.is_recurring,
        "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in c.labels] if c.labels else [],
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    } for c in items]


@router.post("/api/contents", tags=["contents"])
async def create_content(request: Request, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    data = await request.json()
    content = Content(
        title=data["title"],
        description=data.get("description", ""),
        content_type=data["content_type"],
        status=data.get("status", "ideia"),
        responsible_id=data.get("responsible_id"),
        campaign_id=data.get("campaign_id"),
        due_date=to_date(data.get("due_date")),
        priority=data.get("priority", "media"),
        column_order=data.get("column_order", 0),
    )
    db.add(content)
    db.flush()

    if content.due_date:
        auto_create_event(db, f"[Conteudo] {content.title}",
                          content.due_date, source="conteudo",
                          event_type="conteudo", content_id=content.id,
                          description=f"Tipo: {content.content_type} | Status: {content.status}")
    db.commit()
    db.refresh(content)
    return {"id": content.id, "title": content.title}


@router.put("/api/contents/{content_id}", tags=["contents"])
async def update_content(content_id: int, request: Request,
                         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(content, key):
            if key == "due_date":
                val = to_date(val)
            setattr(content, key, val)

    if content.due_date:
        remove_auto_events(db, source="conteudo", content_id=content.id)
        auto_create_event(db, f"[Conteudo] {content.title}",
                          content.due_date, source="conteudo",
                          event_type="conteudo", content_id=content.id,
                          description=f"Tipo: {content.content_type} | Status: {content.status}")
    db.commit()
    return {"ok": True}


@router.delete("/api/contents/{content_id}", tags=["contents"])
async def delete_content(content_id: int, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    remove_auto_events(db, source="conteudo", content_id=content.id)
    db.delete(content)
    db.commit()
    return {"ok": True}


@router.put("/api/contents/{content_id}/move", tags=["contents"])
async def move_content(content_id: int, request: Request,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    data = await request.json()
    content.status = data["status"]
    content.column_order = data.get("order", 0)
    db.commit()
    return {"ok": True}


@router.put("/api/contents/{content_id}/favorite", tags=["contents"])
async def toggle_favorite(content_id: int, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    content.is_favorite = not content.is_favorite
    db.commit()
    return {"ok": True, "is_favorite": content.is_favorite}


@router.post("/api/contents/{content_id}/duplicate", tags=["contents"])
async def duplicate_content(content_id: int, db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    original = db.query(Content).filter(Content.id == content_id).first()
    if not original:
        return {"error": "Conteudo nao encontrado"}
    clone = Content(
        title=f"[Copia] {original.title}",
        description=original.description,
        content_type=original.content_type,
        status="ideia",
        responsible_id=original.responsible_id,
        campaign_id=original.campaign_id,
        due_date=original.due_date,
        priority=original.priority,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return {"id": clone.id, "title": clone.title}
