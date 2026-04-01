from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Campaign, Content

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/timeline", response_class=HTMLResponse)
async def timeline_page(request: Request, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    return templates.TemplateResponse("timeline.html", {
        "request": request, "user": user, "page": "timeline",
    })


@router.get("/api/timeline", tags=["timeline"])
async def timeline_data(db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    campaigns = db.query(Campaign).order_by(Campaign.start_date).all()

    result = []
    for camp in campaigns:
        contents_list = []
        for c in camp.contents:
            contents_list.append({
                "id": c.id,
                "title": c.title,
                "content_type": c.content_type,
                "status": c.status,
                "due_date": c.due_date.isoformat() if c.due_date else None,
            })

        result.append({
            "id": camp.id,
            "name": camp.name,
            "color": camp.color,
            "start_date": camp.start_date.isoformat() if camp.start_date else None,
            "end_date": camp.end_date.isoformat() if camp.end_date else None,
            "status": camp.status,
            "contents": contents_list,
        })

    return result
