from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import User, Idea, Content
from app.auth import get_current_user
from app.calendar_helper import auto_create_event
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ideias", response_class=HTMLResponse)
async def ideas_page(request: Request, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    return templates.TemplateResponse("ideas.html", {
        "request": request, "user": user, "page": "ideias",
    })


@router.get("/api/ideas", tags=["ideas"])
async def list_ideas(search: str = None, tag: str = None,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Idea)
    if search:
        query = query.filter(
            Idea.title.contains(search) | Idea.description.contains(search)
        )
    if tag:
        query = query.filter(Idea.tags.contains(tag))
    items = query.order_by(Idea.created_at.desc()).all()
    return [{
        "id": i.id, "title": i.title, "description": i.description,
        "tags": i.tags, "created_by": i.created_by,
        "creator_name": i.created_by_user.full_name if i.created_by_user else None,
        "is_converted": i.is_converted,
        "converted_content_id": i.converted_content_id,
        "created_at": i.created_at.isoformat(),
    } for i in items]


@router.post("/api/ideas", tags=["ideas"])
async def create_idea(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    data = await request.json()
    idea = Idea(
        title=data["title"],
        description=data.get("description", ""),
        tags=data.get("tags", ""),
        created_by=user.id,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return {"id": idea.id, "title": idea.title}


@router.post("/api/ideas/{idea_id}/convert", tags=["ideas"])
async def convert_idea(idea_id: int, request: Request,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        return {"error": "Ideia nao encontrada"}

    data = await request.json()
    content = Content(
        title=idea.title,
        description=idea.description,
        content_type=data.get("content_type", "post"),
        status="ideia",
        responsible_id=data.get("responsible_id"),
        priority=data.get("priority", "media"),
        due_date=to_date(data.get("due_date")),
    )
    db.add(content)
    db.flush()

    idea.is_converted = True
    idea.converted_content_id = content.id

    auto_create_event(db, f"[Ideia Convertida] {idea.title}",
                      content.due_date or date.today(), source="ideia",
                      event_type="conteudo", content_id=content.id,
                      description=f"Ideia convertida em {content.content_type}")
    db.commit()
    return {"id": content.id, "title": content.title}


@router.delete("/api/ideas/{idea_id}", tags=["ideas"])
async def delete_idea(idea_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        return {"error": "Ideia nao encontrada"}
    db.delete(idea)
    db.commit()
    return {"ok": True}
