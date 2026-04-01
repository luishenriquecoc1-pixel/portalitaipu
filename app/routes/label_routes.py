from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Label, Content

router = APIRouter()


@router.get("/api/labels", tags=["labels"])
async def list_labels(db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    labels = db.query(Label).order_by(Label.name).all()
    return [{
        "id": l.id, "name": l.name, "color": l.color,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in labels]


@router.post("/api/labels", tags=["labels"])
async def create_label(request: Request, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    data = await request.json()
    label = Label(
        name=data["name"],
        color=data.get("color", "#6366f1"),
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return {"id": label.id, "name": label.name, "color": label.color}


@router.delete("/api/labels/{label_id}", tags=["labels"])
async def delete_label(label_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        return {"error": "Label nao encontrada"}
    db.delete(label)
    db.commit()
    return {"ok": True}


@router.post("/api/contents/{content_id}/labels", tags=["labels"])
async def add_label_to_content(content_id: int, request: Request,
                               db: Session = Depends(get_db),
                               user: User = Depends(get_current_user)):
    data = await request.json()
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    label = db.query(Label).filter(Label.id == data["label_id"]).first()
    if not label:
        return {"error": "Label nao encontrada"}
    if label not in content.labels:
        content.labels.append(label)
        db.commit()
    return {"ok": True}


@router.delete("/api/contents/{content_id}/labels/{label_id}", tags=["labels"])
async def remove_label_from_content(content_id: int, label_id: int,
                                    db: Session = Depends(get_db),
                                    user: User = Depends(get_current_user)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        return {"error": "Conteudo nao encontrado"}
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        return {"error": "Label nao encontrada"}
    if label in content.labels:
        content.labels.remove(label)
        db.commit()
    return {"ok": True}
