export type UserRole = 'admin' | 'inspector' | 'viewer';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  designation?: string;
  badge_number?: string;
  is_active: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface BoundingBox {
  x: number; // percentage
  y: number;
  width: number;
  height: number;
}

export interface OCRToken {
  id?: string;
  text: string;
  bbox: BoundingBox;
  confidence: number;
  engine: string;
  needs_review: boolean;
  image_index?: number;
}

export interface ClusteredBlock {
  block_id: string;
  text: string;
  bbox: BoundingBox;
  confidence: number;
  token_count?: number;
  needs_review?: boolean;
  image_index?: number;
}

export interface ExtractedFieldItem {
  field_key: string;
  label: string;
  value?: string | null;
  raw_text?: string | null;
  status: 'found' | 'missing' | 'invalid' | 'review_required';
  confidence: number;
  bbox?: BoundingBox | null;
  image_index?: number;
  image_url?: string | null;
  validation_remarks?: string | null;
  calculated_height_mm?: number | null;
  required_min_height_mm?: number | null;
  cross_referenced?: boolean;
  regex_recovered?: boolean;
  name?: string | null;
  address?: string | null;
}

export interface RuleResultItem {
  rule_id: string;
  clause_reference: string;
  title: string;
  description: string;
  field_key: string;
  status: 'PASS' | 'FAIL' | 'NEEDS_REVIEW';
  severity: 'MANDATORY_VIOLATION' | 'WARNING' | 'INFORMATIVE';
  remarks: string;
  extracted_value?: string | null;
  bbox?: BoundingBox | null;
  confidence: number;
  image_index?: number;
  cross_referenced?: boolean;
}

export interface ComplianceQRItem {
  location_description?: string;
  nearby_text: string;
  classification?: string;
  target_url?: string;
  code_to_enter?: string;
  classification_reason?: string;
}

export interface ScanJobStatus {
  id: string;
  status: 'PENDING' | 'PREPROCESSING' | 'OCR_RUNNING' | 'GEMINI_ANALYSIS' | 'EXTRACTING' | 'RULES_ENGINE' | 'EVALUATING' | 'VISUAL_AUDIT' | 'ANALYZING' | 'AWAITING_QR_EVIDENCE' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress_percentage: number;
  current_stage_message: string;
  created_at: string;
  completed_at?: string | null;
  detected_qr_url?: string | null;
  code_to_enter?: string | null;
  awaiting_qr_since?: string | null;
  available_compliance_qrs?: ComplianceQRItem[] | null;
  batch_code_confidence?: 'high' | 'low' | null;
  batch_code_flag?: string | null;
}

export interface UspCrossVerification {
  mrp_numeric?: number;
  quantity_numeric?: number;
  quantity_unit?: string;
  calculated_usp_per_base_unit?: number;
  calculated_usp_unit?: string;
  declared_usp_raw?: string;
  declared_usp_numeric?: number;
  is_mathematically_accurate?: boolean;
  discrepancy_amount?: number;
  denomination_compliant?: boolean;
  is_compliant?: boolean;
  remarks?: string;
  violations?: string[];
}

export interface SecondScheduleShrinkflationAudit {
  is_second_schedule_commodity?: boolean;
  matched_commodity_category?: string;
  declared_quantity?: string;
  is_standard_prescribed_pack_size?: boolean;
  prescribed_pack_sizes_sample?: string[];
  nearest_standard_pack_size?: string;
  shrinkage_percentage?: number;
  is_compliant?: boolean;
  remarks?: string;
}

export interface Rule13QuantityAudit {
  raw_quantity_text?: string;
  declared_magnitude?: number;
  declared_unit?: string;
  magnitude_rule_compliant?: boolean;
  has_banned_count_terms?: boolean;
  banned_count_terms_found?: string[];
  is_si_unit?: boolean;
  number_symbol_compliant?: boolean;
  has_misleading_qualifiers?: boolean;
  misleading_qualifiers_found?: string[];
  is_rule_13_compliant?: boolean;
  rule_13_violations?: string[];
}

export interface ManufacturerDetails {
  resolution_method?: string;
  resolved_manufacturer_name?: string;
  resolved_address?: string;
  batch_code_used?: string | null;
  is_compliant?: boolean;
  compliance_remarks?: string;
}

export interface MasterComplianceReport {
  product_name?: string;
  total_images_analyzed?: number;
  batch_number?: string;
  qr_code_detected_url?: string | null;
  mandatory_declarations?: Record<string, any>;
  manufacturer_details?: ManufacturerDetails;
  importer_details?: Record<string, any>;
  rule_13_quantity_audit?: Rule13QuantityAudit;
  usp_cross_verification?: UspCrossVerification;
  second_schedule_shrinkflation_audit?: SecondScheduleShrinkflationAudit;
  overall_compliance?: string;
  statutory_summary?: string[];
  visual_and_metrology_audit?: {
    rule_7_font_size?: {
      measured_numeral_height_mm?: number | null;
      statutory_min_height_mm?: number;
      status?: string;
      is_compliant?: boolean;
      rule?: string;
      remarks?: string;
    };
    rule_9_color_contrast?: {
      contrast_ratio?: string;
      is_compliant?: boolean;
      rule?: string;
      remarks?: string;
    };
  };
}

export interface ScanJobResult {
  id: string;
  product_id?: number | null;
  product_name?: string;
  brand_name?: string | null;
  category?: string;
  inspector_id?: number | null;
  inspector_name?: string;
  image_url: string;
  back_image_url?: string | null;
  image_urls?: string[];
  cross_referenced_fields?: string[];
  reference_scale_mm?: number | null;
  status: string;
  progress_percentage: number;
  current_stage_message: string;
  overall_compliance_verdict: 'COMPLIANT' | 'NON_COMPLIANT' | 'FLAGGED_FOR_REVIEW' | 'NEEDS_MANUAL_INSPECTION' | 'PENDING';
  compliance_score: number;
  extracted_data: Record<string, ExtractedFieldItem | any>;
  rule_results: RuleResultItem[];
  raw_ocr_tokens: OCRToken[];
  clustered_blocks?: ClusteredBlock[];
  master_report?: MasterComplianceReport;
  pdf_report_url?: string | null;
  docx_report_url?: string | null;
  inspector_notes?: string | null;
  edited_fields?: Record<string, {
    original_value?: string;
    edited_value: string;
    edited_by?: string;
    edited_by_role?: string;
    edited_at?: string;
  }>;
  detected_qr_url?: string | null;
  code_to_enter?: string | null;
  qr_evidence_url?: string | null;
  available_compliance_qrs?: ComplianceQRItem[] | null;
  created_at: string;
  completed_at?: string | null;
}

export interface Product {
  id: number;
  product_name: string;
  brand_name?: string | null;
  category: string;
  manufacturer_name?: string | null;
  declared_net_quantity?: string | null;
  declared_mrp?: string | null;
  barcode?: string | null;
  latest_compliance_status: string;
  inspection_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProductHistoryItem {
  scan_id: string;
  created_at: string;
  status: string;
  compliance_score: number;
  overall_compliance_verdict: string;
  inspector_name?: string | null;
  violations_count: number;
  image_url: string;
}

export interface DashboardStats {
  total_inspections: number;
  overall_compliance_rate: number;
  mandatory_violations_count: number;
  active_inspectors: number;
  metrics: Array<{
    label: string;
    value: string;
    change?: string;
    trend?: 'up' | 'down' | 'neutral';
  }>;
  violation_trends: Array<{
    date: string;
    total_scans: number;
    compliant: number;
    violations: number;
  }>;
  category_breakdown: Array<{
    category: string;
    inspections: number;
    violations: number;
    compliance_rate: number;
  }>;
  top_violation_types: Array<{
    rule_id: string;
    title: string;
    clause: string;
    count: number;
    percentage: number;
  }>;
  inspector_stats: Array<{
    inspector_name: string;
    badge_number: string;
    inspections_count: number;
    violations_detected: number;
  }>;
  recent_scans: Array<{
    id: string;
    product_name: string;
    category: string;
    created_at: string;
    verdict: string;
    compliance_score: number;
    inspector_name: string;
    violations_count: number;
  }>;
}

export interface RuleConfig {
  id: number;
  rule_id: string;
  clause_reference: string;
  title: string;
  description: string;
  field_key: string;
  severity: string;
  is_active: boolean;
  parameters: Record<string, any>;
  updated_at: string;
}
