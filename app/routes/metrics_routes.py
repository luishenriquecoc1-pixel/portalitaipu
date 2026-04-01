from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Campaign, Content
from app.auth import get_current_user
from app.calendar_helper import auto_create_event, remove_auto_events
from app.date_utils import to_date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CAMPAIGN_STATUSES = ["planejamento", "ativa", "pausada", "finalizada"]


@router.get("/campanhas", response_class=HTMLResponse)
async def campaigns_page(request: Request, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    return templates.TemplateResponse("campaigns.html", {
        "request": request, "user": user, "page": "campanhas",
        "statuses": CAMPAIGN_STATUSES,
    })


@router.get("/api/campaigns", tags=["campaigns"])
async def list_campaigns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    result = []
    for c in items:
        content_count = db.query(Content).filter(Content.campaign_id == c.id).count()
        posted_count = db.query(Content).filter(Content.campaign_id == c.id, Content.status == "postado").count()
        result.append({
            "id": c.id, "name": c.name, "description": c.description,
            "start_date": c.start_date.isoformat(), "end_date": c.end_date.isoformat(),
            "budget": c.budget, "status": c.status, "color": c.color,
            "content_count": content_count, "posted_count": posted_count,
        })
    return result


@router.post("/api/campaigns", tags=["campaigns"])
async def create_campaign(request: Request, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    data = await request.json()
    campaign = Campaign(
        name=data["name"],
        description=data.get("description", ""),
        start_date=to_date(data["start_date"]),
        end_date=to_date(data["end_date"]),
        budget=data.get("budget", 0),
        status=data.get("status", "planejamento"),
        color=data.get("color", "#6366f1"),
    )
    db.add(campaign)
    db.flush()

    auto_create_event(db, f"[Campanha Inicio] {campaign.name}",
                      campaign.start_date, source="campanha",
                      event_type="campanha", campaign_id=campaign.id,
                      color=campaign.color,
                      description=f"Inicio da campanha: {campaign.name}")
    auto_create_event(db, f"[Campanha Fim] {campaign.name}",
                      campaign.end_date, source="campanha",
                      event_type="campanha", campaign_id=campaign.id,
                      color=campaign.color,
                      description=f"Encerramento da campanha: {campaign.name}")
    db.commit()
    db.refresh(campaign)
    return {"id": campaign.id, "name": campaign.name}


@router.put("/api/campaigns/{campaign_id}", tags=["campaigns"])
async def update_campaign(campaign_id: int, request: Request,
                          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"error": "Campanha nao encontrada"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(campaign, key):
            if key in ("start_date", "end_date"):
                val = to_date(val)
            setattr(campaign, key, val)

    remove_auto_events(db, source="campanha", campaign_id=campaign.id)
    auto_create_event(db, f"[Campanha Inicio] {campaign.name}",
                      campaign.start_date, source="campanha",
                      event_type="campanha", campaign_id=campaign.id,
                      color=campaign.color,
                      description=f"Inicio da campanha: {campaign.name}")
    auto_create_event(db, f"[Campanha Fim] {campaign.name}",
                      campaign.end_date, source="campanha",
                      event_type="campanha", campaign_id=campaign.id,
                      color=campaign.color,
                      description=f"Encerramento da campanha: {campaign.name}")
    db.commit()
    return {"ok": True}


@router.delete("/api/campaigns/{campaign_id}", tags=["campaigns"])
async def delete_campaign(campaign_id: int, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"error": "Campanha nao encontrada"}
    remove_auto_events(db, source="campanha", campaign_id=campaign.id)
    db.delete(campaign)
    db.commit()
    return {"ok": True}
