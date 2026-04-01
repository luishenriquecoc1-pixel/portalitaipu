from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Inspiration

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/inspiracoes", response_class=HTMLResponse)
async def inspirations_page(request: Request, db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    return templates.TemplateResponse("inspirations.html", {
        "request": request, "user": user, "page": "inspiracoes",
    })


@router.get("/api/inspirations", tags=["inspirations"])
async def list_inspirations(search: str = None, tag: str = None,
                            db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    query = db.query(Inspiration)
    if search:
        query = query.filter(
            (Inspiration.title.contains(search)) |
            (Inspiration.description.contains(search))
        )
    if tag:
        query = query.filter(Inspiration.tags.contains(tag))

    items = query.order_by(Inspiration.created_at.desc()).all()
    return [{
        "id": i.id, "title": i.title, "url": i.url,
        "description": i.description, "tags": i.tags,
        "found_by": i.found_by,
        "found_by_name": i.found_by_user.full_name if i.found_by_user else None,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    } for i in items]


@router.post("/api/inspirations", tags=["inspirations"])
async def create_inspiration(request: Request, db: Session = Depends(get_db),
                             user: User = Depends(get_current_user)):
    data = await request.json()
    inspiration = Inspiration(
        title=data["title"],
        url=data.get("url", ""),
        description=data.get("description", ""),
        tags=data.get("tags", ""),
        found_by=user.id,
    )
    db.add(inspiration)
    db.commit()
    db.refresh(inspiration)
    return {
        "id": inspiration.id, "title": inspiration.title,
        "url": inspiration.url, "description": inspiration.description,
        "tags": inspiration.tags, "found_by": inspiration.found_by,
        "found_by_name": user.full_name,
    }


@router.delete("/api/inspirations/{inspiration_id}", tags=["inspirations"])
async def delete_inspiration(inspiration_id: int, db: Session = Depends(get_db),
                             user: User = Depends(get_current_user)):
    item = db.query(Inspiration).filter(Inspiration.id == inspiration_id).first()
    if not item:
        return {"error": "Inspiracao nao encontrada"}
    db.delete(item)
    db.commit()
    return {"ok": True}
