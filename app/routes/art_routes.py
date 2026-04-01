import os
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ArtRequest, Content
from app.auth import get_current_user
from app.calendar_helper import auto_create_event, remove_auto_events
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

ART_STATUSES = ["enviado", "andamento", "revisao", "aprovado"]
FORMAT_TYPES = ["feed", "story", "banner", "thumbnail", "capa", "email", "outro"]
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
UPLOAD_DIR = os.path.join("app", "static", "uploads", "arts")


@router.get("/artes", response_class=HTMLResponse)
async def arts_page(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    contents = db.query(Content).all()
    return templates.TemplateResponse("arts.html", {
        "request": request, "user": user, "page": "artes",
        "contents": contents, "statuses": ART_STATUSES, "format_types": FORMAT_TYPES,
    })


@router.get("/api/arts", tags=["arts"])
async def list_arts(status: str = None, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    query = db.query(ArtRequest)
    if status:
        query = query.filter(ArtRequest.status == status)
    items = query.order_by(ArtRequest.updated_at.desc()).all()
    return [{
        "id": a.id, "title": a.title, "description": a.description,
        "references": a.references, "deadline": a.deadline.isoformat() if a.deadline else None,
        "status": a.status, "content_id": a.content_id,
        "format_type": a.format_type, "dimensions": a.dimensions,
        "designer_name": a.designer_name, "feedback": a.feedback,
        "image_path": a.image_path,
        "created_at": a.created_at.isoformat(),
    } for a in items]


@router.post("/api/arts", tags=["arts"])
async def create_art(request: Request, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    data = await request.json()
    art = ArtRequest(
        title=data["title"],
        description=data["description"],
        references=data.get("references", ""),
        deadline=to_date(data["deadline"]),
        status=data.get("status", "enviado"),
        content_id=data.get("content_id"),
        format_type=data.get("format_type", "feed"),
        dimensions=data.get("dimensions", ""),
        designer_name=data.get("designer_name", ""),
    )
    db.add(art)
    db.flush()

    auto_create_event(db, f"[Arte] {art.title}",
                      art.deadline, source="arte",
                      event_type="arte",
                      description=f"Designer: {art.designer_name or 'N/A'} | Formato: {art.format_type}")
    db.commit()
    db.refresh(art)
    return {"id": art.id, "title": art.title}


@router.put("/api/arts/{art_id}", tags=["arts"])
async def update_art(art_id: int, request: Request,
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    art = db.query(ArtRequest).filter(ArtRequest.id == art_id).first()
    if not art:
        return {"error": "Arte nao encontrada"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(art, key) and key != "image_path":
            setattr(art, key, val)
    db.commit()
    return {"ok": True}


@router.delete("/api/arts/{art_id}", tags=["arts"])
async def delete_art(art_id: int, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    art = db.query(ArtRequest).filter(ArtRequest.id == art_id).first()
    if not art:
        return {"error": "Arte nao encontrada"}
    if art.image_path:
        filepath = os.path.join("app", "static", art.image_path.lstrip("/static/"))
        if os.path.exists(filepath):
            os.remove(filepath)
    db.delete(art)
    db.commit()
    return {"ok": True}


@router.post("/api/arts/{art_id}/upload", tags=["arts"])
async def upload_art_image(art_id: int, file: UploadFile = File(...),
                           db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    art = db.query(ArtRequest).filter(ArtRequest.id == art_id).first()
    if not art:
        return {"error": "Arte nao encontrada"}

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": f"Formato nao permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"}

    if art.image_path:
        old_path = os.path.join("app", "static", art.image_path.lstrip("/static/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{art_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    art.image_path = f"/static/uploads/arts/{filename}"
    db.commit()
    return {"ok": True, "image_path": art.image_path}


@router.delete("/api/arts/{art_id}/image", tags=["arts"])
async def delete_art_image(art_id: int, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    art = db.query(ArtRequest).filter(ArtRequest.id == art_id).first()
    if not art:
        return {"error": "Arte nao encontrada"}
    if art.image_path:
        filepath = os.path.join("app", "static", art.image_path.lstrip("/static/"))
        if os.path.exists(filepath):
            os.remove(filepath)
        art.image_path = None
        db.commit()
    return {"ok": True}
