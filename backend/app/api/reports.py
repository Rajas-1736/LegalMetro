import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scan_job import ScanJob
from app.models.user import User
from app.core.dependencies import get_current_user, require_inspector_or_admin
from app.reports.pdf_generator import pdf_report_generator
from app.reports.docx_generator import docx_report_generator
from app.storage.minio_client import storage_service

router = APIRouter(prefix="/reports", tags=["Reports"])

def _build_report_payload(scan: ScanJob) -> dict:
    extracted = scan.extracted_data or {}
    master_report = extracted.get("master_report") or extracted

    # Ensure sub-audits exist in master_report for template lookups
    if "usp_cross_verification" not in master_report and "usp_cross_verification" in extracted:
        master_report["usp_cross_verification"] = extracted["usp_cross_verification"]
    if "second_schedule_shrinkflation_audit" not in master_report and "second_schedule_shrinkflation_audit" in extracted:
        master_report["second_schedule_shrinkflation_audit"] = extracted["second_schedule_shrinkflation_audit"]
    if "visual_and_metrology_audit" not in master_report and "visual_and_metrology_audit" in extracted:
        master_report["visual_and_metrology_audit"] = extracted["visual_and_metrology_audit"]

    # Filter statutory_summary so compliance affirmations are never treated as violations
    raw_summary = master_report.get("statutory_summary") or extracted.get("statutory_summary") or []
    clean_summary = [
        item for item in raw_summary
        if "comply strictly" not in item.lower() and "no statutory" not in item.lower() and "nil" not in item.lower()
    ]
    master_report["statutory_summary"] = clean_summary
    if "statutory_summary" in extracted:
        extracted["statutory_summary"] = clean_summary

    prod_name = (
        (scan.product.product_name if scan.product else None)
        or extracted.get("product_name", {}).get("value")
        or master_report.get("product_name")
        or "Packaged Commodity"
    )

    return {
        "id": scan.id,
        "created_at": scan.created_at,
        "product_name": prod_name,
        "category": scan.product.category if scan.product else "Packaged Goods",
        "inspector_name": scan.inspector.full_name if scan.inspector else "Senior Inspector",
        "reference_scale_mm": scan.reference_scale_mm,
        "overall_compliance_verdict": scan.overall_compliance_verdict,
        "compliance_score": scan.compliance_score,
        "rule_results": scan.rule_results or [],
        "extracted_data": extracted,
        "master_report": master_report,
        "cross_referenced_fields": scan.cross_referenced_fields or extracted.get("cross_referenced_fields", []),
        "image_urls": scan.image_urls or ([scan.image_url] if scan.image_url else []),
        "inspector_notes": scan.inspector_notes,
        "edited_fields": scan.edited_fields or {}
    }

@router.post("/{scan_id}/generate")
def generate_reports(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector_or_admin)
):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    payload = _build_report_payload(scan)

    # Generate PDF
    pdf_bytes = pdf_report_generator.generate(payload)
    pdf_url = storage_service.upload_file(pdf_bytes, f"report_{scan.id}.pdf", content_type="application/pdf")
    scan.pdf_report_url = pdf_url

    # Generate DOCX
    docx_bytes = docx_report_generator.generate(payload)
    docx_url = storage_service.upload_file(
        docx_bytes,
        f"report_{scan.id}.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    scan.docx_report_url = docx_url

    db.commit()

    return {
        "scan_id": scan.id,
        "pdf_report_url": pdf_url,
        "docx_report_url": docx_url,
        "message": "PDF and DOCX compliance reports successfully generated."
    }

@router.get("/{scan_id}/download/pdf")
def download_pdf_report(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    payload = _build_report_payload(scan)
    pdf_bytes = pdf_report_generator.generate(payload)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VisionX_Report_{scan_id[:8]}.pdf"}
    )

@router.get("/{scan_id}/download/docx")
def download_docx_report(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    payload = _build_report_payload(scan)
    docx_bytes = docx_report_generator.generate(payload)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=VisionX_Report_{scan_id[:8]}.docx"}
    )

@router.post("/{scan_id}/attach-evidence")
async def attach_evidence_photo(
    scan_id: str,
    evidence_image: UploadFile = File(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector_or_admin)
):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    img_bytes = await evidence_image.read()
    evidence_filename = f"evidence_{scan_id}_{evidence_image.filename}"
    evidence_url = storage_service.upload_file(img_bytes, evidence_filename, evidence_image.content_type or "image/jpeg")

    existing_notes = scan.inspector_notes or ""
    additional_note = f"\n[Evidence Attached: {evidence_image.filename} - Notes: {notes}]"
    scan.inspector_notes = existing_notes + additional_note
    scan.back_image_url = evidence_url
    db.commit()

    return {"message": "Evidence successfully attached", "evidence_url": evidence_url}
