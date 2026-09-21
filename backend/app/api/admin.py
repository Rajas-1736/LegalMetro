from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.rule_config import RuleConfig
from app.schemas.rule import RuleConfigResponse, RuleConfigUpdate
import os
import json
from app.core.dependencies import require_admin

DEFAULT_RULES_JSON = os.path.join(os.path.dirname(__file__), "..", "rules", "legal_metrology_2011.json")

def load_default_rules():
    try:
        with open(DEFAULT_RULES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

router = APIRouter(prefix="/admin", tags=["Admin & Rule Management"])

@router.get("/rules", response_model=List[RuleConfigResponse])
def get_all_rules(db: Session = Depends(get_db)):
    rules = db.query(RuleConfig).order_by(RuleConfig.id.asc()).all()
    # If DB is empty, sync from default json rules
    if not rules:
        for r in load_default_rules():
            db_rule = RuleConfig(
                rule_id=r["rule_id"],
                clause_reference=r["clause_reference"],
                title=r["title"],
                description=r["description"],
                field_key=r["field_key"],
                severity=r.get("severity", "MANDATORY_VIOLATION"),
                is_active=r.get("is_active", True),
                parameters=r.get("parameters", {})
            )
            db.add(db_rule)
        db.commit()
        rules = db.query(RuleConfig).order_by(RuleConfig.id.asc()).all()
    
    return rules

@router.put("/rules/{rule_id}", response_model=RuleConfigResponse)
def update_rule(
    rule_id: str,
    update_data: RuleConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    rule = db.query(RuleConfig).filter(RuleConfig.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    if update_data.title is not None:
        rule.title = update_data.title
    if update_data.description is not None:
        rule.description = update_data.description
    if update_data.severity is not None:
        rule.severity = update_data.severity
    if update_data.is_active is not None:
        rule.is_active = update_data.is_active
    if update_data.parameters is not None:
        rule.parameters = update_data.parameters

    db.commit()
    db.refresh(rule)

    return rule
