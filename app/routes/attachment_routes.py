import os
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Attachment

router = APIRouter()

UPLOAD_DIR = "app/static/uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg",
                      ".jpeg", ".gif", ".mp4", ".mov", ".zip"}


@router.get("/api/contents/{content_id}/attachments", tags=["attachments"])
async def list_attachments(content_id: int, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    items = db.query(Attachment).filter(
        Attachment.content_id == content_id
    ).order_by(Attachment.created_at.desc()).all()

    return [{
        "id": a.id, "content_id": a.content_id,
        "filename": a.filename, "file_path": a.file_path,
        "file_size": a.file_size, "file_type": a.file_type,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in items]


@router.post("/api/contents/{content_id}/attachments", tags=["attachments"])
async def upload_attachment(content_id: int, file: UploadFile = File(...),
                            db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,
                            detail=f"Extensao {ext} nao permitida. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}")

    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{content_id}_{unique_id}_{file.filename}"
    file_path_disk = os.path.join(UPLOAD_DIR, safe_filename)

    contents = await file.read()
    with open(file_path_disk, "wb") as f:
        f.write(contents)

    file_size = len(contents)
    file_path_url = f"/static/uploads/attachments/{safe_filename}"

    attachment = Attachment(
        content_id=content_id,
        filename=file.filename,
        file_path=file_path_url,
        file_size=file_size,
        file_type=ext.lstrip("."),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "id": attachment.id, "content_id": attachment.content_id,
        "filename": attachment.filename, "file_path": attachment.file_path,
        "file_size": attachment.file_size, "file_type": attachment.file_type,
    }


@router.delete("/api/attachments/{attachment_id}", tags=["attachments"])
async def delete_attachment(attachment_id: int, db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        return {"error": "Anexo nao encontrado"}

    # Remove file from disk
    disk_path = attachment.file_path.lstrip("/")
    if os.path.exists(disk_path):
        os.remove(disk_path)

    db.delete(attachment)
    db.commit()
    return {"ok": True}
