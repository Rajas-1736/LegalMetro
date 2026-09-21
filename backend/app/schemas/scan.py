from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class BoundingBox(BaseModel):
    x: float  # Percentage 0.0 to 100.0
    y: float
    width: float
    height: float

class OCRToken(BaseModel):
    id: Optional[str] = None
    text: str
    bbox: BoundingBox
    confidence: float
    engine: str
    needs_review: bool = False
    image_index: int = 0
    image_url: Optional[str] = None

class ClusteredBlock(BaseModel):
    block_id: str
    text: str
    bbox: BoundingBox
    confidence: float
    token_count: Optional[int] = None
    needs_review: bool = False
    image_index: int = 0
    image_url: Optional[str] = None

class ExtractedFieldItem(BaseModel):
    field_key: str
    label: str
    value: Optional[str] = None
    raw_text: Optional[str] = None
    status: str = "found"  # found, missing, invalid, review_required
    confidence: float = 0.0
    bbox: Optional[BoundingBox] = None
    image_index: Optional[int] = 0
    image_url: Optional[str] = None
    validation_remarks: Optional[str] = None
    calculated_height_mm: Optional[float] = None
    required_min_height_mm: Optional[float] = None
    cross_referenced: bool = False
    regex_recovered: bool = False
    name: Optional[str] = None  # for separated manufacturer name
    address: Optional[str] = None  # for separated manufacturer address

class RuleResultItem(BaseModel):
    rule_id: str
    clause_reference: str
    title: str
    description: str
    field_key: str
    status: str  # PASS, FAIL, NEEDS_REVIEW
    severity: str  # MANDATORY_VIOLATION, WARNING, INFORMATIVE
    remarks: str
    extracted_value: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    image_index: Optional[int] = 0
    image_url: Optional[str] = None
    cross_referenced: bool = False
    confidence: float = 1.0

class ScanJobStatusResponse(BaseModel):
    id: str
    status: str  # PENDING, PREPROCESSING, OCR_RUNNING, EXTRACTING, EVALUATING, AWAITING_QR_EVIDENCE, PROCESSING, COMPLETED, FAILED
    progress_percentage: int
    current_stage_message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    detected_qr_url: Optional[str] = None
    code_to_enter: Optional[str] = None
    awaiting_qr_since: Optional[datetime] = None
    available_compliance_qrs: Optional[List[Dict[str, Any]]] = None
    batch_code_confidence: Optional[str] = None
    batch_code_flag: Optional[str] = None

class ScanJobResultResponse(BaseModel):
    id: str
    product_id: Optional[int] = None
    product_name: Optional[str] = "Packaged Product"
    brand_name: Optional[str] = None
    category: Optional[str] = "Packaged Commodity"
    inspector_id: Optional[int] = None
    inspector_name: Optional[str] = None
    image_url: str
    image_urls: List[str] = []
    back_image_url: Optional[str] = None
    reference_scale_mm: Optional[float] = None
    
    status: str
    progress_percentage: int
    current_stage_message: str
    overall_compliance_verdict: str  # COMPLIANT, NON_COMPLIANT, FLAGGED_FOR_REVIEW
    compliance_score: float
    
    extracted_data: Dict[str, Any]
    rule_results: List[RuleResultItem]
    raw_ocr_tokens: List[OCRToken]
    clustered_blocks: Optional[List[ClusteredBlock]] = None
    cross_referenced_fields: List[str] = []
    
    pdf_report_url: Optional[str] = None
    docx_report_url: Optional[str] = None
    inspector_notes: Optional[str] = None
    edited_fields: Optional[Dict[str, Any]] = None
    detected_qr_url: Optional[str] = None
    code_to_enter: Optional[str] = None
    qr_evidence_url: Optional[str] = None
    available_compliance_qrs: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanJobEditFieldRequest(BaseModel):
    field_key: str
    new_value: str
    revert: bool = False

