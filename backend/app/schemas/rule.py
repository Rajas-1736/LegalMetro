from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class RuleConfigBase(BaseModel):
    rule_id: str
    clause_reference: str
    title: str
    description: str
    field_key: str
    severity: str
    is_active: bool = True
    parameters: Dict[str, Any] = {}

class RuleConfigUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

class RuleConfigResponse(RuleConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
