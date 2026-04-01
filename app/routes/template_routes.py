import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, CampaignTemplate, Campaign, Content
from app.date_utils import to_date

router = APIRouter()


@router.get("/api/campaign-templates", tags=["templates"])
async def list_templates(db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    templates = db.query(CampaignTemplate).order_by(
        CampaignTemplate.created_at.desc()
    ).all()
    return [{
        "id": t.id, "name": t.name, "description": t.description,
        "template_data": json.loads(t.template_data) if t.template_data else {},
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in templates]


@router.post("/api/campaign-templates", tags=["templates"])
async def create_template(request: Request, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    data = await request.json()
    campaign = db.query(Campaign).filter(Campaign.id == data["campaign_id"]).first()
    if not campaign:
        return {"error": "Campanha nao encontrada"}

    contents_data = []
    for c in campaign.contents:
        contents_data.append({
            "content_type": c.content_type,
            "priority": c.priority,
            "title": c.title,
        })

    template_data = {
        "campaign": {
            "name": campaign.name,
            "description": campaign.description,
            "budget": campaign.budget,
            "status": campaign.status,
            "color": campaign.color,
        },
        "contents": contents_data,
    }

    template = CampaignTemplate(
        name=data["name"],
        description=data.get("description", ""),
        template_data=json.dumps(template_data, ensure_ascii=False),
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "id": template.id, "name": template.name,
        "description": template.description,
        "template_data": template_data,
    }


@router.post("/api/campaign-templates/{template_id}/apply", tags=["templates"])
async def apply_template(template_id: int, request: Request,
                         db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    template = db.query(CampaignTemplate).filter(
        CampaignTemplate.id == template_id
    ).first()
    if not template:
        return {"error": "Template nao encontrado"}

    data = await request.json()
    tpl = json.loads(template.template_data)
    camp_data = tpl.get("campaign", {})

    campaign = Campaign(
        name=camp_data.get("name", template.name),
        description=camp_data.get("description", ""),
        start_date=to_date(data.get("start_date")),
        end_date=to_date(data.get("end_date")),
        budget=camp_data.get("budget", 0),
        status=camp_data.get("status", "planejamento"),
        color=camp_data.get("color", "#6366f1"),
    )
    db.add(campaign)
    db.flush()

    contents_created = []
    for ct in tpl.get("contents", []):
        content = Content(
            title=ct.get("title", "Sem titulo"),
            content_type=ct.get("content_type", "post"),
            priority=ct.get("priority", "media"),
            campaign_id=campaign.id,
            status="ideia",
        )
        db.add(content)
        contents_created.append(content)

    db.commit()
    db.refresh(campaign)

    return {
        "id": campaign.id, "name": campaign.name,
        "contents_count": len(contents_created),
    }


@router.delete("/api/campaign-templates/{template_id}", tags=["templates"])
async def delete_template(template_id: int, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    template = db.query(CampaignTemplate).filter(
        CampaignTemplate.id == template_id
    ).first()
    if not template:
        return {"error": "Template nao encontrado"}
    db.delete(template)
    db.commit()
    return {"ok": True}
