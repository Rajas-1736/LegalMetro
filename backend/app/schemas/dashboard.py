from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class MetricCard(BaseModel):
    label: str
    value: str
    change: Optional[str] = None
    trend: Optional[str] = "up" # up, down, neutral

class ViolationTrendPoint(BaseModel):
    date: str
    total_scans: int
    compliant: int
    violations: int

class CategoryViolationItem(BaseModel):
    category: str
    inspections: int
    violations: int
    compliance_rate: float

class TopViolationTypeItem(BaseModel):
    rule_id: str
    title: str
    clause: str
    count: int
    percentage: float

class InspectorActivityItem(BaseModel):
    inspector_name: str
    badge_number: str
    inspections_count: int
    violations_detected: int

class RecentScanItem(BaseModel):
    id: str
    product_name: str
    category: str
    created_at: datetime
    verdict: str
    compliance_score: float
    inspector_name: str
    violations_count: int

class DashboardStatsResponse(BaseModel):
    total_inspections: int
    overall_compliance_rate: float
    mandatory_violations_count: int
    active_inspectors: int
    metrics: List[MetricCard]
    violation_trends: List[ViolationTrendPoint]
    category_breakdown: List[CategoryViolationItem]
    top_violation_types: List[TopViolationTypeItem]
    inspector_stats: List[InspectorActivityItem]
    recent_scans: List[RecentScanItem]
