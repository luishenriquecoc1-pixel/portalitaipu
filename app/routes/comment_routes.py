from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Comment

router = APIRouter()


@router.get("/api/comments", tags=["comments"])
async def list_comments(content_id: int = None, art_id: int = None,
                        db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    query = db.query(Comment)
    if content_id:
        query = query.filter(Comment.content_id == content_id)
    elif art_id:
        query = query.filter(Comment.art_id == art_id)
    else:
        return []

    comments = query.order_by(Comment.created_at).all()
    return [{
        "id": c.id,
        "content_id": c.content_id,
        "art_id": c.art_id,
        "user_id": c.user_id,
        "user_name": c.user.full_name if c.user else None,
        "user_avatar_color": c.user.avatar_color if c.user else "#6366f1",
        "text": c.text,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in comments]


@router.post("/api/comments", tags=["comments"])
async def create_comment(request: Request, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    data = await request.json()
    comment = Comment(
        content_id=data.get("content_id"),
        art_id=data.get("art_id"),
        user_id=user.id,
        text=data["text"],
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "content_id": comment.content_id,
        "art_id": comment.art_id,
        "user_id": comment.user_id,
        "user_name": user.full_name,
        "user_avatar_color": user.avatar_color,
        "text": comment.text,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


@router.delete("/api/comments/{comment_id}", tags=["comments"])
async def delete_comment(comment_id: int, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return {"error": "Comentario nao encontrado"}
    db.delete(comment)
    db.commit()
    return {"ok": True}
