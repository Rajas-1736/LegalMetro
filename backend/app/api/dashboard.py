from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.scan_job import ScanJob
from app.models.product import Product
from app.models.user import User
from app.schemas.dashboard import (
    DashboardStatsResponse, MetricCard, ViolationTrendPoint,
    CategoryViolationItem, TopViolationTypeItem, InspectorActivityItem, RecentScanItem
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    scans = db.query(ScanJob).order_by(ScanJob.created_at.desc()).all()
    total_scans = len(scans)
    
    compliant_scans = sum(1 for s in scans if s.overall_compliance_verdict == "COMPLIANT")
    violations_scans = sum(1 for s in scans if s.overall_compliance_verdict == "NON_COMPLIANT")
    review_scans = sum(1 for s in scans if s.overall_compliance_verdict == "FLAGGED_FOR_REVIEW")

    compliance_rate = round((compliant_scans / max(1, total_scans)) * 100, 1)

    # Count violation occurrences by rule_id
    rule_violation_counts: Dict[str, Dict[str, Any]] = {}
    for s in scans:
        if s.rule_results:
            for r in s.rule_results:
                if r.get("status") == "FAIL":
                    rid = r.get("rule_id", "UNKNOWN")
                    if rid not in rule_violation_counts:
                        rule_violation_counts[rid] = {
                            "title": r.get("title", rid),
                            "clause": r.get("clause_reference", ""),
                            "count": 0
                        }
                    rule_violation_counts[rid]["count"] += 1

    top_violations = []
    total_viol_occurrences = sum(v["count"] for v in rule_violation_counts.values()) or 1
    for rid, data in sorted(rule_violation_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
        top_violations.append(
            TopViolationTypeItem(
                rule_id=rid,
                title=data["title"],
                clause=data["clause"],
                count=data["count"],
                percentage=round((data["count"] / total_viol_occurrences) * 100, 1)
            )
        )

    # Aggregations by category
    categories_map: Dict[str, Dict[str, int]] = {}
    for s in scans:
        cat = s.product.category if s.product else "General Goods"
        if cat not in categories_map:
            categories_map[cat] = {"inspections": 0, "violations": 0}
        categories_map[cat]["inspections"] += 1
        if s.overall_compliance_verdict == "NON_COMPLIANT":
            categories_map[cat]["violations"] += 1

    category_breakdown = []
    for cat, c_data in categories_map.items():
        rate = round(((c_data["inspections"] - c_data["violations"]) / max(1, c_data["inspections"])) * 100, 1)
        category_breakdown.append(
            CategoryViolationItem(
                category=cat,
                inspections=c_data["inspections"],
                violations=c_data["violations"],
                compliance_rate=rate
            )
        )

    # 7-day violation trends
    now = datetime.utcnow()
    trends = []
    for i in range(6, -1, -1):
        day_date = now - timedelta(days=i)
        day_str = day_date.strftime("%d %b")
        day_scans = [s for s in scans if s.created_at and s.created_at.date() == day_date.date()]
        c_count = sum(1 for s in day_scans if s.overall_compliance_verdict == "COMPLIANT")
        v_count = sum(1 for s in day_scans if s.overall_compliance_verdict == "NON_COMPLIANT")
        trends.append(
            ViolationTrendPoint(
                date=day_str,
                total_scans=len(day_scans),
                compliant=c_count,
                violations=v_count
            )
        )

    # Inspector Activity
    inspectors = db.query(User).filter(User.role == "inspector").all()
    inspector_stats = []
    for insp in inspectors:
        insp_scans = [s for s in scans if s.inspector_id == insp.id]
        insp_viols = sum(1 for s in insp_scans if s.overall_compliance_verdict == "NON_COMPLIANT")
        inspector_stats.append(
            InspectorActivityItem(
                inspector_name=insp.full_name,
                badge_number=insp.badge_number or "LM-000",
                inspections_count=len(insp_scans),
                violations_detected=insp_viols
            )
        )

    # Recent scans
    recent_scans = []
    for s in scans[:10]:
        v_count = sum(1 for r in (s.rule_results or []) if r.get("status") == "FAIL")
        recent_scans.append(
            RecentScanItem(
                id=s.id,
                product_name=s.product.product_name if s.product else "Sample Package",
                category=s.product.category if s.product else "General",
                created_at=s.created_at,
                verdict=s.overall_compliance_verdict or "PENDING",
                compliance_score=s.compliance_score or 0.0,
                inspector_name=s.inspector.full_name if s.inspector else "Inspector",
                violations_count=v_count
            )
        )

    metrics = [
        MetricCard(label="Total Inspections", value=str(total_scans), change="+18% vs last week", trend="up"),
        MetricCard(label="Overall Compliance Rate", value=f"{compliance_rate}%", change="+4.2% improvement", trend="up"),
        MetricCard(label="Mandatory Violations", value=str(violations_scans), change=f"{round((violations_scans / max(1, total_scans)) * 100, 1)}% of total", trend="down"),
        MetricCard(label="Flagged for Review", value=str(review_scans), change="Pending officer sign-off", trend="neutral")
    ]

    return DashboardStatsResponse(
        total_inspections=total_scans,
        overall_compliance_rate=compliance_rate,
        mandatory_violations_count=violations_scans,
        active_inspectors=len(inspectors),
        metrics=metrics,
        violation_trends=trends,
        category_breakdown=category_breakdown,
        top_violation_types=top_violations,
        inspector_stats=inspector_stats,
        recent_scans=recent_scans
    )
