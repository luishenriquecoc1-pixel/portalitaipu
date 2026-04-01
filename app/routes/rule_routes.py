from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, AutomationRule, Content, ArtRequest, Video

router = APIRouter()


def execute_rules(db: Session, model_name: str, field_name: str, new_value: str):
    """Execute automation rules that match the given trigger.

    Called from other routes when a status (or other field) changes.
    Finds active rules matching the trigger and applies the configured action.
    """
    rules = db.query(AutomationRule).filter(
        AutomationRule.is_active == True,
        AutomationRule.trigger_model == model_name,
        AutomationRule.trigger_field == field_name,
        AutomationRule.trigger_value == new_value,
    ).all()

    for rule in rules:
        action_model = rule.action_model
        action_field = rule.action_field
        action_value = rule.action_value

        if action_model == "conteudo":
            items = db.query(Content).all()
            for item in items:
                if hasattr(item, action_field):
                    setattr(item, action_field, action_value)
        elif action_model == "arte":
            items = db.query(ArtRequest).all()
            for item in items:
                if hasattr(item, action_field):
                    setattr(item, action_field, action_value)
        elif action_model == "video":
            items = db.query(Video).all()
            for item in items:
                if hasattr(item, action_field):
                    setattr(item, action_field, action_value)

    if rules:
        db.commit()


@router.get("/api/rules", tags=["rules"])
async def list_rules(db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    rules = db.query(AutomationRule).order_by(AutomationRule.created_at.desc()).all()
    return [{
        "id": r.id, "name": r.name,
        "trigger_model": r.trigger_model,
        "trigger_field": r.trigger_field,
        "trigger_value": r.trigger_value,
        "action_model": r.action_model,
        "action_field": r.action_field,
        "action_value": r.action_value,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rules]


@router.post("/api/rules", tags=["rules"])
async def create_rule(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    data = await request.json()
    rule = AutomationRule(
        name=data["name"],
        trigger_model=data["trigger_model"],
        trigger_field=data["trigger_field"],
        trigger_value=data["trigger_value"],
        action_model=data["action_model"],
        action_field=data["action_field"],
        action_value=data["action_value"],
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {
        "id": rule.id, "name": rule.name,
        "trigger_model": rule.trigger_model,
        "trigger_field": rule.trigger_field,
        "trigger_value": rule.trigger_value,
        "action_model": rule.action_model,
        "action_field": rule.action_field,
        "action_value": rule.action_value,
        "is_active": rule.is_active,
    }


@router.put("/api/rules/{rule_id}", tags=["rules"])
async def update_rule(rule_id: int, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not rule:
        return {"error": "Regra nao encontrada"}
    data = await request.json()
    for key, val in data.items():
        if hasattr(rule, key):
            setattr(rule, key, val)
    db.commit()
    return {"ok": True}


@router.delete("/api/rules/{rule_id}", tags=["rules"])
async def delete_rule(rule_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not rule:
        return {"error": "Regra nao encontrada"}
    db.delete(rule)
    db.commit()
    return {"ok": True}
