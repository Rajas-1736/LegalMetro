import os
import shutil
import tempfile
import logging
from typing import Dict, Any, Callable, Optional, List, Union, Tuple
from app.pipeline.multi_panel_scanner import (
    run_master_inspection,
    GeminiQuotaExhaustedError,
    GeminiRateLimitError,
)
from app.pipeline import rules_engine

logger = logging.getLogger(__name__)

def convert_master_report_to_rule_results(
    master_report: Dict[str, Any],
    image_urls: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], str, float, List[str]]:
    """
    Translates the canonical multimodal MasterComplianceReport into backwards-compatible
    RuleResultItem representations and computes the compliance score and overall verdict.
    """
    rule_results: List[Dict[str, Any]] = []
    cross_referenced_fields: List[str] = []
    
    mand = master_report.get("mandatory_declarations", {})
    mfg = master_report.get("manufacturer_details", {})
    q_audit = master_report.get("rule_13_quantity_audit", {})
    usp_audit = master_report.get("usp_cross_verification", {})
    shrink_audit = master_report.get("second_schedule_shrinkflation_audit", {})
    metro_audit = master_report.get("visual_and_metrology_audit", {})
    font_audit = metro_audit.get("rule_7_font_size", {})
    contrast_audit = metro_audit.get("rule_9_color_contrast", {})

    # Helper for panel index lookup
    def get_panel_idx(panel_str: Optional[str]) -> int:
        if not panel_str:
            return 0
        p_lower = panel_str.lower()
        if "panel 2" in p_lower or "base" in p_lower or "bottom" in p_lower or "side" in p_lower:
            return 1
        return 0

    def get_panel_url(panel_idx: int) -> Optional[str]:
        if image_urls and 0 <= panel_idx < len(image_urls):
            return image_urls[panel_idx]
        return image_urls[0] if image_urls else None

    # 1. Rule 6(1)(a): Manufacturer / Packer / Importer Name & Address
    mfg_method = mfg.get("resolution_method", "ON_PACK")
    mfg_compliant = mfg.get("is_compliant", False)
    mfg_name = mfg.get("resolved_manufacturer_name")
    mfg_addr = mfg.get("resolved_address")
    if mfg_name and mfg_addr and mfg_name != "UNRESOLVED" and not str(mfg_addr).startswith("UNRESOLVED"):
        mfg_extracted = f"{mfg_name} - {mfg_addr}"
    elif mfg_addr and mfg_addr != "UNRESOLVED":
        mfg_extracted = mfg_addr
    elif mfg_name and mfg_name != "UNRESOLVED":
        mfg_extracted = mfg_name
    else:
        mfg_extracted = mfg_addr or mfg_name or "Not detected"
    mfg_is_cr = mfg_method in ["QR_PORTAL_ATTENDED", "CRIMP_CODE", "PANEL_POINTER"]
    if mfg_is_cr:
        cross_referenced_fields.append("manufacturer_details")

    if mfg_compliant:
        mfg_status = "PASS"
        mfg_severity = "MANDATORY_VIOLATION"
    elif mfg_method in ["QR_PORTAL_ATTENDED_REQUIRED", "UNRESOLVED", "NO_BATCH_CODE_ON_PACKAGE"] or mfg.get("compliance_status") == "NEEDS_MANUAL_INSPECTION":
        mfg_status = "NEEDS_REVIEW"
        mfg_severity = "WARNING"
    else:
        mfg_status = "FAIL"
        mfg_severity = "MANDATORY_VIOLATION"

    rule_results.append({
        "rule_id": "RULE_6_1_A",
        "clause_reference": "Rule 6(1)(a)",
        "title": "Name & Complete Address of Manufacturer / Packer",
        "description": "Every package must conspicuously declare the full legal name and complete physical address of the manufacturer or packer.",
        "field_key": "manufacturer_name",
        "status": mfg_status,
        "severity": mfg_severity,
        "remarks": mfg.get("compliance_remarks", "Manufacturer identification audit complete."),
        "extracted_value": mfg_extracted,
        "bbox": None,
        "image_index": 0,
        "image_url": get_panel_url(0),
        "cross_referenced": mfg_is_cr,
        "confidence": 0.95
    })

    # 2. Rule 6(1)(b): Generic Name of Commodity
    gen = mand.get("generic_commodity_name", {})
    gen_val = gen.get("declared_value")
    gen_comp = gen.get("is_compliant", False)
    gen_idx = get_panel_idx(gen.get("found_on_panel"))
    rule_results.append({
        "rule_id": "RULE_6_1_B",
        "clause_reference": "Rule 6(1)(b)",
        "title": "Generic or Common Name of Commodity",
        "description": "The generic or common name of the commodity must be conspicuously stated on the principal display panel.",
        "field_key": "generic_name",
        "status": "PASS" if gen_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": gen.get("compliance_remarks", "Generic name verification complete."),
        "extracted_value": gen_val,
        "bbox": None,
        "image_index": gen_idx,
        "image_url": get_panel_url(gen_idx),
        "cross_referenced": False,
        "confidence": 0.95
    })

    # 3. Rule 6(1)(c) & Rule 13: Net Quantity & Standard SI Units Audit
    net_q = mand.get("net_quantity", {})
    net_val = net_q.get("declared_value")
    net_comp = net_q.get("is_compliant", False) and q_audit.get("is_rule_13_compliant", True)
    q_violations = q_audit.get("rule_13_violations", [])
    q_remarks = net_q.get("compliance_remarks", "")
    if q_violations:
        q_remarks = f"{q_remarks} [Rule 13 Violations: {', '.join(q_violations)}]"
    elif not q_remarks:
        q_remarks = "Net quantity complies with Rule 6(1)(c) and Rule 13 SI unit mandates."
    net_idx = get_panel_idx(net_q.get("found_on_panel"))
    net_is_cr = net_idx > 0 or "panel" in str(net_q.get("found_on_panel", "")).lower()
    if net_is_cr:
        cross_referenced_fields.append("net_quantity")

    rule_results.append({
        "rule_id": "RULE_6_1_C_AND_13",
        "clause_reference": "Rule 6(1)(c) & Rule 13",
        "title": "Net Quantity & Standard SI Units Audit",
        "description": "Net quantity in standard SI units (g, kg, ml, L) without non-standard qualifiers (e.g., 'gms', 'approx').",
        "field_key": "net_quantity",
        "status": "PASS" if net_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": q_remarks,
        "extracted_value": net_val,
        "bbox": None,
        "image_index": net_idx,
        "image_url": get_panel_url(net_idx),
        "cross_referenced": net_is_cr,
        "confidence": 0.95
    })

    # 4. Rule 6(1)(d): Month and Year of Manufacture / Pre-packing & Proviso Exemption
    mfg_date = mand.get("mfg_or_pkd_date", {})
    date_val = mfg_date.get("declared_value")
    date_comp = mfg_date.get("is_compliant", False)
    date_stat = mfg_date.get("compliance_status", "NON_COMPLIANT")
    date_ref = mfg_date.get("rule_reference", "Rule 6(1)(d)")
    date_idx = get_panel_idx(mfg_date.get("found_on_panel"))
    date_is_cr = date_idx > 0 or "crimp" in str(mfg_date.get("compliance_remarks", "")).lower() or "base" in str(mfg_date.get("compliance_remarks", "")).lower()
    if date_is_cr:
        cross_referenced_fields.append("mfg_or_pkd_date")

    rule_results.append({
        "rule_id": "RULE_6_1_D",
        "clause_reference": date_ref,
        "title": "Month & Year of Manufacture / Packing / Import (or Proviso Exemption)",
        "description": "The month and year of pre-packing or manufacture must be clearly declared. Batch numbers cannot substitute for dates. Statutory exemption applies to incense sticks (agarbatti) and bidis under Rule 6(1) second proviso.",
        "field_key": "mfg_date",
        "status": "PASS" if date_comp else ("NEEDS_REVIEW" if date_stat == "NEEDS_MANUAL_INSPECTION" else "FAIL"),
        "severity": "MANDATORY_VIOLATION",
        "remarks": mfg_date.get("compliance_remarks", "Date declaration verification complete."),
        "extracted_value": date_val,
        "bbox": None,
        "image_index": date_idx,
        "image_url": get_panel_url(date_idx),
        "cross_referenced": date_is_cr,
        "confidence": 0.95
    })

    # 5. Rule 6(1)(e): Maximum Retail Price (MRP)
    mrp_decl = mand.get("mrp", {})
    mrp_val = mrp_decl.get("declared_value")
    mrp_comp = mrp_decl.get("is_compliant", False)
    mrp_idx = get_panel_idx(mrp_decl.get("found_on_panel"))
    mrp_is_cr = mrp_idx > 0 or "base" in str(mrp_decl.get("compliance_remarks", "")).lower()
    if mrp_is_cr:
        cross_referenced_fields.append("mrp")

    rule_results.append({
        "rule_id": "RULE_6_1_E",
        "clause_reference": "Rule 6(1)(e)",
        "title": "Maximum Retail Price (Inclusive of all taxes)",
        "description": "MRP must be declared conspicuously with the mandatory phrase 'inclusive of all taxes'.",
        "field_key": "mrp",
        "status": "PASS" if mrp_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": mrp_decl.get("compliance_remarks", "MRP verification complete."),
        "extracted_value": mrp_val,
        "bbox": None,
        "image_index": mrp_idx,
        "image_url": get_panel_url(mrp_idx),
        "cross_referenced": mrp_is_cr,
        "confidence": 0.95
    })

    # 6. Rule 6(1)(e) Second Proviso: Unit Sale Price (USP) Mathematical Verification
    usp_comp = usp_audit.get("is_compliant", True)
    usp_decl = mand.get("unit_sale_price", {})
    usp_val = usp_audit.get("declared_usp_raw") or usp_decl.get("declared_value") or "Not declared"
    rule_results.append({
        "rule_id": "RULE_6_1_E_USP",
        "clause_reference": "Rule 6(1)(e) Second Proviso",
        "title": "Unit Sale Price (USP) Mathematical Cross-Verification",
        "description": "USP must be declared per g/ml/piece and must mathematically equal (MRP / Net Quantity).",
        "field_key": "unit_sale_price",
        "status": "PASS" if usp_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": usp_audit.get("remarks", "USP mathematical cross-check complete."),
        "extracted_value": usp_val,
        "bbox": None,
        "image_index": get_panel_idx(usp_decl.get("found_on_panel")),
        "image_url": get_panel_url(get_panel_idx(usp_decl.get("found_on_panel"))),
        "cross_referenced": False,
        "confidence": 0.95
    })

    # 7. Rule 6(1)(f): Consumer Care Contact Details
    cc_decl = mand.get("consumer_care_details", {})
    cc_val = cc_decl.get("declared_value")
    cc_comp = cc_decl.get("is_compliant", False)
    cc_idx = get_panel_idx(cc_decl.get("found_on_panel"))
    rule_results.append({
        "rule_id": "RULE_6_1_F",
        "clause_reference": "Rule 6(1)(f)",
        "title": "Consumer Care Helpline, Email & Physical Address",
        "description": "Package must state the name, address, telephone number and email address of the consumer care official.",
        "field_key": "consumer_care",
        "status": "PASS" if cc_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": cc_decl.get("compliance_remarks", "Consumer care contact verification complete."),
        "extracted_value": cc_val,
        "bbox": None,
        "image_index": cc_idx,
        "image_url": get_panel_url(cc_idx),
        "cross_referenced": False,
        "confidence": 0.95
    })

    # 8. Rule 6(1)(g): Country of Origin
    co_decl = mand.get("country_of_origin", {})
    co_val = co_decl.get("declared_value")
    co_comp = co_decl.get("is_compliant", False)
    co_idx = get_panel_idx(co_decl.get("found_on_panel"))
    rule_results.append({
        "rule_id": "RULE_6_1_G",
        "clause_reference": "Rule 6(1)(g)",
        "title": "Country of Origin for Domestic or Imported Goods",
        "description": "Every package must clearly state the country of origin.",
        "field_key": "country_of_origin",
        "status": "PASS" if co_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION",
        "remarks": co_decl.get("compliance_remarks", "Country of origin verification complete."),
        "extracted_value": co_val,
        "bbox": None,
        "image_index": co_idx,
        "image_url": get_panel_url(co_idx),
        "cross_referenced": False,
        "confidence": 0.95
    })

    # 9. Rule 5: Second Schedule Anti-Shrinkflation Pack Sizes
    shrink_comp = shrink_audit.get("is_compliant", True)
    is_sched_2 = shrink_audit.get("is_second_schedule_commodity", False)
    shrink_decl = shrink_audit.get("declared_quantity") or net_val or "N/A"
    rule_results.append({
        "rule_id": "RULE_5_SHRINKFLATION",
        "clause_reference": "Rule 5 & Second Schedule",
        "title": "Second Schedule Prescribed Pack Sizes (Anti-Shrinkflation)",
        "description": "Commodities listed in the Second Schedule must be packed only in prescribed standard package sizes.",
        "field_key": "standard_pack_size",
        "status": "PASS" if shrink_comp else "FAIL",
        "severity": "MANDATORY_VIOLATION" if is_sched_2 else "INFORMATIVE",
        "remarks": shrink_audit.get("remarks", "Second Schedule standard pack size check complete."),
        "extracted_value": f"{shrink_decl} (Category: {shrink_audit.get('matched_commodity_category', 'Not restricted')})",
        "bbox": None,
        "image_index": 0,
        "image_url": get_panel_url(0),
        "cross_referenced": False,
        "confidence": 0.95
    })

    # 10. Rule 7: Minimum Numeral Font Height
    font_comp = font_audit.get("is_compliant", True)
    font_stat = font_audit.get("status", "COMPLIANT")
    font_measured = font_audit.get("measured_numeral_height_mm")
    font_min = font_audit.get("statutory_min_height_mm")
    font_val = f"{font_measured} mm (Min: {font_min} mm)" if font_measured is not None else "Manual scale required"
    font_res_stat = "PASS" if (font_comp and font_stat == "COMPLIANT") else ("NEEDS_REVIEW" if font_stat == "NEEDS_MANUAL_INSPECTION" else "FAIL")
    rule_results.append({
        "rule_id": "RULE_7_FONT_SIZE",
        "clause_reference": "Rule 7(2) read with Table-I",
        "title": "Statutory Minimum Numeral Height Table-I",
        "description": "Minimum numeral and letter height scaled to principal display panel area.",
        "field_key": "font_size",
        "status": font_res_stat,
        "severity": "MANDATORY_VIOLATION",
        "remarks": font_audit.get("remarks", "Font size metrology verification complete."),
        "extracted_value": font_val,
        "bbox": None,
        "image_index": 0,
        "image_url": get_panel_url(0),
        "cross_referenced": False,
        "confidence": 0.90
    })

    # 11. Rule 9: Conspicuous Color Contrast
    cont_comp = contrast_audit.get("is_compliant", True)
    cont_ratio = contrast_audit.get("contrast_ratio", "N/A")
    rule_results.append({
        "rule_id": "RULE_9_CONTRAST",
        "clause_reference": "Rule 9(1)(b)",
        "title": "Conspicuous Background Color Contrast",
        "description": "All declarations must be clearly visible and contrast conspicuously with the background.",
        "field_key": "color_contrast",
        "status": "PASS" if cont_comp else "FAIL",
        "severity": "WARNING",
        "remarks": contrast_audit.get("remarks", "Color contrast visual metrology check complete."),
        "extracted_value": f"Ratio: {cont_ratio}",
        "bbox": None,
        "image_index": 0,
        "image_url": get_panel_url(0),
        "cross_referenced": False,
        "confidence": 0.90
    })

    # Compute overall compliance verdict and score
    mandatory_fails = [
        r for r in rule_results
        if r["status"] == "FAIL" and r["severity"] == "MANDATORY_VIOLATION"
    ]
    reviews = [r for r in rule_results if r["status"] == "NEEDS_REVIEW"]
    passes = [r for r in rule_results if r["status"] == "PASS"]

    if mandatory_fails:
        verdict = "NON_COMPLIANT"
    elif reviews:
        verdict = "FLAGGED_FOR_REVIEW"
    else:
        verdict = "COMPLIANT"

    # Score out of 100
    total_eval = len(rule_results)
    score_points = len(passes) + (len(reviews) * 0.5)
    compliance_score = round((score_points / total_eval) * 100.0, 1)

    return rule_results, verdict, compliance_score, sorted(list(set(cross_referenced_fields)))


class PipelineManager:
    """
    Master Compliance Pipeline Manager
    Integrates the Google Gemini Multimodal Compliance Engine with deterministic
    Policy-as-Code rules (LMR 2011), Rule 13 SI verification, USP cross-checks,
    Second Schedule shrinkflation audit, and visual metrology.
    """

    def run_pipeline(
        self,
        images_input: Union[bytes, List[bytes], str, List[str]],
        reference_width_mm: Optional[float] = None,
        image_urls: Optional[List[str]] = None,
        qr_portal_screenshot_path: Optional[str] = None,
        skip_qr_verification: bool = False,
        no_batch_code_present: bool = False,
        batch_code_override: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, str], None]] = None
    ) -> Dict[str, Any]:
        temp_dir: Optional[str] = None
        saved_paths: List[str] = []

        try:
            # 1. Normalize images input to local disk file paths
            if isinstance(images_input, (str, os.PathLike)):
                saved_paths = [str(images_input)]
            elif isinstance(images_input, list) and images_input and isinstance(images_input[0], (str, os.PathLike)):
                saved_paths = [str(p) for p in images_input]
            else:
                # Byte stream inputs: write to isolated temp directory
                temp_dir = tempfile.mkdtemp(prefix="visionx_scan_")
                raw_list = [images_input] if isinstance(images_input, bytes) else images_input
                for idx, img_b in enumerate(raw_list):
                    t_path = os.path.join(temp_dir, f"panel_{idx+1}.jpg")
                    with open(t_path, "wb") as f:
                        f.write(img_b)
                    saved_paths.append(t_path)

            total_panels = len(saved_paths)
            urls = image_urls or ["" for _ in range(total_panels)]
            while len(urls) < total_panels:
                urls.append("")

            # Stage A: Preprocessing & Normalization
            if progress_callback:
                progress_callback(
                    "PREPROCESSING",
                    15,
                    f"Stage A: Image Preprocessing - Normalizing {total_panels} panel image(s) and checking QR markers..."
                )

            # Stage B: Multimodal Vision Inspection via VisionX Engine
            if progress_callback:
                progress_callback(
                    "GEMINI_ANALYSIS",
                    40,
                    f"Stage B: VisionX Multimodal Engine - Analyzing packaging declarations across panels..."
                )

            # Stage C: Statutory Rule Verification (2011 Rules) & Cross-Panel Reconciliation
            if progress_callback:
                progress_callback(
                    "RULES_ENGINE",
                    65,
                    "Stage C: Statutory Rule Verification (2011 Rules) - Reconciling cross-panel declarations..."
                )

            # Execute Master Inspection Pipeline
            master_report = run_master_inspection(
                image_paths=saved_paths,
                reference_scale_mm=reference_width_mm,
                qr_portal_screenshot_path=qr_portal_screenshot_path,
                skip_qr_verification=skip_qr_verification,
                no_batch_code_present=no_batch_code_present,
                batch_code_override=batch_code_override
            )

            # Stage D: Visual & Metrology Audit (Contrast ratio, Table-I font scale, USP cross-check)
            if progress_callback:
                progress_callback(
                    "VISUAL_AUDIT",
                    85,
                    "Stage D: Visual & Metrology Audit - Auditing Table-I font scale & Rule 9(1)(b) contrast..."
                )

            # Convert to UI RuleResultItems
            rule_results, overall_verdict, compliance_score, cross_refs = convert_master_report_to_rule_results(
                master_report, urls
            )

            # Build synthetic OCR tokens from extracted declarations so frontend bounding-box viewers have tokens
            pseudo_tokens: List[Dict[str, Any]] = []
            mand = master_report.get("mandatory_declarations", {})
            token_id = 1
            for k, decl in mand.items():
                val = decl.get("declared_value")
                if val:
                    pseudo_tokens.append({
                        "id": f"token_{token_id}",
                        "text": str(val),
                        "bbox": {"x": 5.0, "y": 5.0 + (token_id * 7.0), "width": 80.0, "height": 5.0},
                        "confidence": 0.95,
                        "engine": "gemini-multimodal",
                        "needs_review": False,
                        "image_index": 0,
                        "image_url": urls[0] if urls else None
                    })
                    token_id += 1

            # Prepare backwards-compatible extracted_data dictionary containing both master report and legacy keys
            mfg_det = master_report.get("manufacturer_details", {})
            mfg_stat = "found" if mfg_det.get("is_compliant") else ("review_required" if mfg_det.get("resolution_method") in ["QR_PORTAL_ATTENDED_REQUIRED", "UNRESOLVED", "NO_BATCH_CODE_ON_PACKAGE"] or mfg_det.get("compliance_status") == "NEEDS_MANUAL_INSPECTION" else "invalid")

            extracted_fields_payload = {
                "product_name": {
                    "label": "Product / Brand Name",
                    "value": master_report.get("product_name"),
                    "status": "found",
                    "confidence": 0.95,
                    "validation_remarks": "Identified from principal display panel."
                },
                "generic_name": {
                    "label": "Common / Generic Commodity Name",
                    "value": mand.get("generic_commodity_name", {}).get("declared_value"),
                    "status": "found" if mand.get("generic_commodity_name", {}).get("is_compliant") else "missing",
                    "confidence": float(str(mand.get("generic_commodity_name", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("generic_commodity_name", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("generic_commodity_name", {}).get("compliance_remarks", "Rule 6(1)(b) verification complete.")
                },
                "manufacturer_name": {
                    "label": "Manufacturer / Packer Legal Name",
                    "value": mfg_det.get("resolved_manufacturer_name"),
                    "status": mfg_stat,
                    "confidence": 0.95,
                    "validation_remarks": mfg_det.get("compliance_remarks", "Rule 6(1)(a) verification complete.")
                },
                "manufacturer_address": {
                    "label": "Complete Physical Factory Address",
                    "value": mfg_det.get("resolved_address"),
                    "status": mfg_stat,
                    "confidence": 0.95,
                    "validation_remarks": mfg_det.get("compliance_remarks", "Rule 6(1)(a) factory premises verification.")
                },
                "net_quantity": {
                    "label": "Net Quantity & Standard SI Units",
                    "value": mand.get("net_quantity", {}).get("declared_value"),
                    "status": "found" if mand.get("net_quantity", {}).get("is_compliant") else "invalid",
                    "confidence": float(str(mand.get("net_quantity", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("net_quantity", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("net_quantity", {}).get("compliance_remarks", "Rule 6(1)(c) & Rule 13 audit.")
                },
                "mrp": {
                    "label": "Maximum Retail Price (MRP)",
                    "value": mand.get("mrp", {}).get("declared_value"),
                    "status": "found" if mand.get("mrp", {}).get("is_compliant") else "invalid",
                    "confidence": float(str(mand.get("mrp", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("mrp", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("mrp", {}).get("compliance_remarks", "Rule 6(1)(e) retail price declaration.")
                },
                "unit_sale_price": {
                    "label": "Unit Sale Price (USP)",
                    "value": mand.get("unit_sale_price", {}).get("declared_value"),
                    "status": "found" if mand.get("unit_sale_price", {}).get("is_compliant") else "missing",
                    "confidence": float(str(mand.get("unit_sale_price", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("unit_sale_price", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("unit_sale_price", {}).get("compliance_remarks", "Rule 6(1)(e) USP mandate.")
                },
                "mfg_date": {
                    "label": "Month & Year of Manufacture / Packing",
                    "value": mand.get("mfg_or_pkd_date", {}).get("declared_value"),
                    "status": "found" if mand.get("mfg_or_pkd_date", {}).get("is_compliant") else "missing",
                    "confidence": float(str(mand.get("mfg_or_pkd_date", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("mfg_or_pkd_date", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("mfg_or_pkd_date", {}).get("compliance_remarks", "Rule 6(1)(d) date declaration.")
                },
                "consumer_care": {
                    "label": "Consumer Care Contact Details",
                    "value": mand.get("consumer_care_details", {}).get("declared_value"),
                    "status": "found" if mand.get("consumer_care_details", {}).get("is_compliant") else "missing",
                    "confidence": float(str(mand.get("consumer_care_details", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("consumer_care_details", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("consumer_care_details", {}).get("compliance_remarks", "Rule 6(1)(f) grievance contact.")
                },
                "country_of_origin": {
                    "label": "Country of Origin",
                    "value": mand.get("country_of_origin", {}).get("declared_value"),
                    "status": "found" if mand.get("country_of_origin", {}).get("is_compliant") else "missing",
                    "confidence": float(str(mand.get("country_of_origin", {}).get("confidence", "95%")).replace("%", "")) / 100.0 if mand.get("country_of_origin", {}).get("confidence") else 0.95,
                    "validation_remarks": mand.get("country_of_origin", {}).get("compliance_remarks", "Rule 6(1)(g) origin declaration.")
                },
                # Complete Canonical Multimodal Report
                "master_report": master_report,
                "usp_cross_verification": master_report.get("usp_cross_verification", {}),
                "second_schedule_shrinkflation_audit": master_report.get("second_schedule_shrinkflation_audit", {}),
                "rule_13_quantity_audit": master_report.get("rule_13_quantity_audit", {}),
                "visual_and_metrology_audit": master_report.get("visual_and_metrology_audit", {}),
                "cross_referenced_fields": cross_refs
            }

            if progress_callback:
                progress_callback(
                    "ANALYZING",
                    90,
                    f"Compliance audit complete: {overall_verdict} (Score: {compliance_score}%). Generating inspection reports..."
                )

            return {
                "image_metadata": {"panel_count": total_panels, "panels": saved_paths},
                "raw_ocr_tokens": pseudo_tokens,
                "clustered_blocks": [],
                "extracted_data": extracted_fields_payload,
                "rule_results": rule_results,
                "overall_compliance_verdict": overall_verdict,
                "compliance_score": compliance_score,
                "cross_referenced_fields": cross_refs,
                "master_report": master_report
            }

        except GeminiQuotaExhaustedError as qe:
            logger.error(f"Gemini scan quota exhausted: {qe}")
            raise
        except GeminiRateLimitError as re_err:
            logger.error(f"Gemini scan rate limit: {re_err}")
            raise
        except Exception as ex:
            logger.exception(f"Pipeline error: {ex}")
            raise
        finally:
            # Clean up temp files if created
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


pipeline_manager = PipelineManager()
