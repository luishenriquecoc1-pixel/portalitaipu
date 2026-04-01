from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.auth import get_current_user
from app.models import User, ChecklistItem

router = APIRouter()


@router.get("/api/contents/{content_id}/checklist", tags=["checklist"])
async def list_checklist(content_id: int, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    items = db.query(ChecklistItem).filter(
        ChecklistItem.content_id == content_id
    ).order_by(ChecklistItem.order).all()

    return [{
        "id": item.id, "content_id": item.content_id,
        "text": item.text, "is_done": item.is_done,
        "order": item.order,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    } for item in items]


@router.post("/api/contents/{content_id}/checklist", tags=["checklist"])
async def create_checklist_item(content_id: int, request: Request,
                                db: Session = Depends(get_db),
                                user: User = Depends(get_current_user)):
    data = await request.json()
    max_order = db.query(func.max(ChecklistItem.order)).filter(
        ChecklistItem.content_id == content_id
    ).scalar()
    next_order = (max_order or 0) + 1

    item = ChecklistItem(
        content_id=content_id,
        text=data["text"],
        order=next_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id, "content_id": item.content_id,
        "text": item.text, "is_done": item.is_done,
        "order": item.order,
    }


@router.put("/api/checklist/{item_id}", tags=["checklist"])
async def update_checklist_item(item_id: int, request: Request,
                                db: Session = Depends(get_db),
                                user: User = Depends(get_current_user)):
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        return {"error": "Item nao encontrado"}
    data = await request.json()
    if "is_done" in data:
        item.is_done = data["is_done"]
    if "text" in data:
        item.text = data["text"]
    if "order" in data:
        item.order = data["order"]
    db.commit()
    return {"ok": True}


@router.delete("/api/checklist/{item_id}", tags=["checklist"])
async def delete_checklist_item(item_id: int, db: Session = Depends(get_db),
                                user: User = Depends(get_current_user)):
    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not item:
        return {"error": "Item nao encontrado"}
    db.delete(item)
    db.commit()
    return {"ok": True}
