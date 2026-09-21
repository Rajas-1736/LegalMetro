import logging
from datetime import datetime
from typing import Optional, List, Union
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.scan_job import ScanJob
from app.models.product import Product
from app.pipeline.pipeline_manager import pipeline_manager
from app.storage.minio_client import storage_service
from app.reports.pdf_generator import pdf_report_generator
from app.reports.docx_generator import docx_report_generator

logger = logging.getLogger(__name__)

def update_job_progress(job_id: str, status: str, progress: int, stage_message: str):
    db = SessionLocal()
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if job:
            job.status = status
            job.progress_percentage = progress
            job.current_stage_message = stage_message
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update progress for job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()

from app.pipeline.multi_panel_scanner import (
    GeminiQuotaExhaustedError,
    GeminiRateLimitError,
    AwaitingQREvidenceException,
)

def execute_scan_pipeline(
    job_id: str,
    images_bytes: Union[bytes, List[bytes]],
    reference_scale_mm: Optional[float] = None,
    image_urls: Optional[List[str]] = None,
    qr_portal_screenshot_path: Optional[str] = None,
    skip_qr_verification: bool = False,
    no_batch_code_present: bool = False,
    batch_code_override: Optional[str] = None
):
    """Core logic that runs the multimodal pipeline across one or multiple panel images."""
    logger.info(f"Starting scan pipeline for job {job_id}")
    
    def on_progress(status: str, progress: int, msg: str):
        update_job_progress(job_id, status, progress, msg)

    try:
        # Run Multimodal Inspection Pipeline
        result = pipeline_manager.run_pipeline(
            images_input=images_bytes,
            reference_width_mm=reference_scale_mm,
            image_urls=image_urls,
            qr_portal_screenshot_path=qr_portal_screenshot_path,
            skip_qr_verification=skip_qr_verification,
            no_batch_code_present=no_batch_code_present,
            batch_code_override=batch_code_override,
            progress_callback=on_progress
        )

        db = SessionLocal()
        try:
            job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in database.")
                return

            job.raw_ocr_tokens = result["raw_ocr_tokens"]
            job.clustered_blocks = result["clustered_blocks"]
            job.extracted_data = result["extracted_data"]
            job.rule_results = result["rule_results"]
            job.cross_referenced_fields = result.get("cross_referenced_fields", [])
            job.overall_compliance_verdict = result["overall_compliance_verdict"]
            job.compliance_score = result["compliance_score"]
            job.status = "COMPLETED"
            job.progress_percentage = 100
            job.current_stage_message = "Scan and compliance evaluation complete."
            job.completed_at = datetime.utcnow()

            # Persist QR traceability metadata to job record
            master_rep = result.get("master_report", {})
            if master_rep.get("qr_code_detected_url"):
                job.detected_qr_url = master_rep.get("qr_code_detected_url")
            mfg_info = master_rep.get("manufacturer_details", {})
            if mfg_info.get("batch_code_used"):
                job.code_to_enter = mfg_info.get("batch_code_used")

            # Update associated product status if present
            if job.product_id:
                product = db.query(Product).filter(Product.id == job.product_id).first()
                if product:
                    product.latest_compliance_status = result["overall_compliance_verdict"]
                    product.inspection_count = (product.inspection_count or 0) + 1
                    
                    extracted = result.get("extracted_data", {})
                    mand_decls = master_rep.get("mandatory_declarations", {})
                    
                    # 1. Product Name
                    gen_name = extracted.get("generic_name", {}).get("value")
                    prod_name = extracted.get("product_name", {}).get("value") or master_rep.get("product_name")
                    if gen_name and str(gen_name).strip() and str(gen_name).strip().lower() != "not detected":
                        product.product_name = str(gen_name).strip()
                    elif prod_name and str(prod_name).strip() and str(prod_name).strip().lower() != "not detected":
                        product.product_name = str(prod_name).strip()
                        
                    # 2. Manufacturer Name
                    mfg_val = extracted.get("manufacturer_name", {}).get("value") or mfg_info.get("resolved_manufacturer_name")
                    if mfg_val and str(mfg_val).strip() and not str(mfg_val).startswith("UNRESOLVED"):
                        product.manufacturer_name = str(mfg_val).strip()

                    # 3. Net Quantity
                    net_qty = (
                        extracted.get("net_quantity", {}).get("value")
                        or mand_decls.get("net_quantity", {}).get("declared_value")
                    )
                    if not net_qty:
                        for r in result.get("rule_results", []):
                            if r.get("rule_id") in ["RULE_6_1_C_AND_13", "RULE_6_1_C"] or r.get("field_key") == "net_quantity":
                                net_qty = r.get("extracted_value")
                                break
                    if net_qty and str(net_qty).strip() and str(net_qty).strip().lower() not in ["not detected", "none", "-", "unresolved"]:
                        product.declared_net_quantity = str(net_qty).strip()

                    # 4. Maximum Retail Price (MRP)
                    mrp_val = (
                        extracted.get("mrp", {}).get("value")
                        or mand_decls.get("mrp", {}).get("declared_value")
                    )
                    if not mrp_val:
                        for r in result.get("rule_results", []):
                            if r.get("rule_id") == "RULE_6_1_E" or r.get("field_key") == "mrp":
                                mrp_val = r.get("extracted_value")
                                break
                    if mrp_val and str(mrp_val).strip() and str(mrp_val).strip().lower() not in ["not detected", "none", "-", "unresolved"]:
                        product.declared_mrp = str(mrp_val).strip()

                    product.updated_at = datetime.utcnow()

            # Prepare scan data payload for report generation
            report_data = {
                "id": job.id,
                "created_at": job.created_at,
                "product_name": (job.product.product_name if job.product else None) or result["extracted_data"].get("product_name", {}).get("value") or "Packaged Commodity",
                "category": job.product.category if job.product else "Packaged Goods",
                "inspector_name": job.inspector.full_name if job.inspector else "Legal Metrology Inspector",
                "reference_scale_mm": job.reference_scale_mm,
                "overall_compliance_verdict": job.overall_compliance_verdict,
                "compliance_score": job.compliance_score,
                "rule_results": job.rule_results,
                "extracted_data": job.extracted_data,
                "master_report": result.get("master_report", {}),
                "inspector_notes": job.inspector_notes,
                "image_urls": job.image_urls or ([job.image_url] if job.image_url else [])
            }

            # Generate PDF
            try:
                pdf_bytes = pdf_report_generator.generate(report_data)
                pdf_url = storage_service.upload_file(
                    pdf_bytes, f"report_{job.id}.pdf", content_type="application/pdf"
                )
                job.pdf_report_url = pdf_url
            except Exception as pe:
                logger.error(f"PDF generation error for job {job_id}: {pe}")

            # Generate DOCX
            try:
                docx_bytes = docx_report_generator.generate(report_data)
                docx_url = storage_service.upload_file(
                    docx_bytes, f"report_{job.id}.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                job.docx_report_url = docx_url
            except Exception as de:
                logger.error(f"DOCX generation error for job {job_id}: {de}")

            db.commit()
            logger.info(f"Scan pipeline completed successfully for job {job_id}")

        finally:
            db.close()

    except AwaitingQREvidenceException as qe:
        logger.info(f"Scan job {job_id} paused awaiting QR evidence: {qe.detected_qr_url}, code: {qe.code_to_enter}")
        db = SessionLocal()
        try:
            job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
            if job:
                job.status = "AWAITING_QR_EVIDENCE"
                job.progress_percentage = 45
                job.current_stage_message = "Manufacturer verification required via QR portal."
                job.detected_qr_url = qe.detected_qr_url
                job.code_to_enter = qe.code_to_enter
                job.awaiting_qr_since = datetime.utcnow()
                extracted = dict(job.extracted_data or {})
                extracted["available_compliance_qrs"] = [
                    q if isinstance(q, dict) else (q.model_dump() if hasattr(q, "model_dump") else dict(q))
                    for q in (qe.available_compliance_qrs or [])
                ]
                extracted["batch_code_confidence"] = qe.batch_code_confidence
                extracted["batch_code_flag"] = qe.batch_code_flag
                job.extracted_data = extracted
                db.commit()
        except Exception as dbe:
            logger.error(f"Failed to record AWAITING_QR_EVIDENCE on job {job_id}: {dbe}")
            db.rollback()
        finally:
            db.close()
    except GeminiQuotaExhaustedError as qe:
        logger.error(f"Gemini scan quota exhausted for job {job_id}: {qe}")
        update_job_progress(job_id, "FAILED", 0, str(qe))
    except GeminiRateLimitError as re_err:
        logger.error(f"Gemini scan rate limit error for job {job_id}: {re_err}")
        update_job_progress(job_id, "FAILED", 0, str(re_err))
    except Exception as ex:
        logger.exception(f"Pipeline error for job {job_id}: {ex}")
        update_job_progress(job_id, "FAILED", 0, f"Processing error: {str(ex)}")

@celery_app.task(name="app.tasks.scan_worker.process_scan_task")
def process_scan_task(
    job_id: str,
    image_filenames: Union[str, List[str]],
    reference_scale_mm: Optional[float] = None,
    qr_portal_screenshot_filename: Optional[str] = None,
    skip_qr_verification: bool = False,
    no_batch_code_present: bool = False,
    batch_code_override: Optional[str] = None
):
    """Celery background task for asynchronous multi-image scanning."""
    filenames = [image_filenames] if isinstance(image_filenames, str) else image_filenames
    image_bytes_list = []
    image_urls = []

    for fn in filenames:
        file_data = storage_service.get_file(fn)
        if file_data:
            img_bytes, _ = file_data
            image_bytes_list.append(img_bytes)
            image_urls.append(f"/api/v1/storage/file/{fn}")

    if not image_bytes_list:
        update_job_progress(job_id, "FAILED", 0, "Uploaded image(s) not found in storage.")
        return

    qr_path = None
    if qr_portal_screenshot_filename:
        qr_data = storage_service.get_file(qr_portal_screenshot_filename)
        if qr_data:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
                tf.write(qr_data[0])
                qr_path = tf.name

    execute_scan_pipeline(
        job_id,
        image_bytes_list,
        reference_scale_mm,
        image_urls=image_urls,
        qr_portal_screenshot_path=qr_path,
        skip_qr_verification=skip_qr_verification,
        no_batch_code_present=no_batch_code_present,
        batch_code_override=batch_code_override
    )
