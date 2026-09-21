from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from app.database import Base

class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(100), unique=True, index=True, nullable=False)
    clause_reference = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    field_key = Column(String(100), nullable=False)
    severity = Column(String(50), default="MANDATORY_VIOLATION", nullable=False) # MANDATORY_VIOLATION, WARNING, INFORMATIVE
    is_active = Column(Boolean, default=True, nullable=False)
    parameters = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
