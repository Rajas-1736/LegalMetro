import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    image_url = Column(String(500), nullable=False)
    image_urls = Column(JSON, default=list) # List of panel image URLs for multi-panel commodities
    back_image_url = Column(String(500), nullable=True)
    cross_referenced_fields = Column(JSON, default=list) # Fields tagged with cross-panel references
    reference_scale_mm = Column(Float, nullable=True)  # user provided physical scale in mm
    
    status = Column(String(50), default="PENDING", index=True) # PENDING, PREPROCESSING, OCR_RUNNING, EXTRACTING, EVALUATING, AWAITING_QR_EVIDENCE, PROCESSING, COMPLETED, FAILED
    progress_percentage = Column(Integer, default=0)
    current_stage_message = Column(String(255), default="Job queued")
    
    # QR Portal Attended Verification fields
    detected_qr_url = Column(String(500), nullable=True)
    code_to_enter = Column(String(50), nullable=True)
    qr_evidence_url = Column(String(500), nullable=True)
    awaiting_qr_since = Column(DateTime, nullable=True)
    
    overall_compliance_verdict = Column(String(50), default="PENDING") # COMPLIANT, NON_COMPLIANT, FLAGGED_FOR_REVIEW
    compliance_score = Column(Float, default=0.0)
    
    # Detailed pipeline outputs
    raw_ocr_tokens = Column(JSON, default=list) # [{text, bbox, confidence, engine, needs_review}]
    clustered_blocks = Column(JSON, default=list) # [{block_id, text, bbox, token_ids}]
    extracted_data = Column(JSON, default=dict) # {manufacturer: {...}, net_quantity: {...}, mrp: {...}, etc.}
    rule_results = Column(JSON, default=list) # [{rule_id, title, status, severity, citation, remarks, confidence, bbox}]
    
    pdf_report_url = Column(String(500), nullable=True)
    docx_report_url = Column(String(500), nullable=True)
    inspector_notes = Column(Text, nullable=True)
    edited_fields = Column(JSON, default=dict) # {field_key: {original_value, edited_value, edited_by, edited_at}}
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="scans")
    inspector = relationship("User")
