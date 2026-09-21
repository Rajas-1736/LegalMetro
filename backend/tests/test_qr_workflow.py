import os
import pytest
from app.pipeline.multi_panel_scanner import (
    detect_qr_code,
    AwaitingQREvidenceException,
    run_master_inspection,
    validate_and_score_batch_code,
)
from app.pipeline.pipeline_manager import convert_master_report_to_rule_results

def test_qr_detection_opencv():
    """Verify that local OpenCV detection locates the QR URL without any API calls."""
    sample_path = os.path.join(os.path.dirname(__file__), "..", "test_samples", "imgqr.jpeg")
    if not os.path.exists(sample_path):
        pytest.skip("imgqr.jpeg not found in test_samples")
    
    qr_url = detect_qr_code([sample_path])
    assert qr_url is not None
    assert "https://" in qr_url
    assert "noice.in" in qr_url

def test_curved_packaging_qr_detection():
    """Verify robust detection on curved/glossy FMCG packaging and URL redirect resolution."""
    sample_path = os.path.join(os.path.dirname(__file__), "..", "test_samples", "biscuit_qr.jpg")
    if not os.path.exists(sample_path):
        pytest.skip("biscuit_qr.jpg not found in test_samples")
    
    qr_url = detect_qr_code([sample_path])
    assert qr_url is not None
    assert "sunfeastworld.com" in qr_url or "delivr.com" in qr_url
    assert "factory-address" in qr_url or "2jdvh-qr" in qr_url

def test_skipped_qr_evidence_rule_results():
    """
    Verify Step 6: When QR portal verification is skipped by the inspector,
    the rule engine must mark Rule 6(1)(a) as NEEDS_REVIEW (not hard FAIL),
    severity WARNING, and overall verdict as NEEDS_MANUAL_INSPECTION.
    """
    mock_master_report = {
        "product_name": "MASALA CHANA DAL",
        "total_images_analyzed": 1,
        "batch_number": "ZFF18G2628",
        "qr_code_detected_url": "https://noice.in/suppliers",
        "mandatory_declarations": {
            "generic_commodity_name": {
                "declared_value": "MASALA CHANA DAL",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "Generic commodity name conspicuously stated."
            },
            "net_quantity": {
                "declared_value": "150 g",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "Declared in standard SI units (g)."
            },
            "mrp": {
                "declared_value": "Rs. 40.00",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "MRP inclusive of all taxes declared."
            },
            "unit_sale_price": {
                "declared_value": "Rs. 0.27 per g",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "USP declared."
            },
            "mfg_or_pkd_date": {
                "declared_value": "12/25",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "Date declared."
            },
            "consumer_care_details": {
                "declared_value": "Care: 1800-000-000, care@example.com",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "Consumer care declared."
            },
            "country_of_origin": {
                "declared_value": "India",
                "found_on_panel": "Front Panel",
                "compliance_status": "COMPLIANT",
                "is_compliant": True,
                "compliance_remarks": "Domestic product."
            }
        },
        "manufacturer_details": {
            "resolution_method": "UNRESOLVED",
            "resolved_manufacturer_name": "UNRESOLVED",
            "resolved_address": "UNRESOLVED",
            "batch_code_used": "ZFF",
            "is_compliant": False,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "compliance_remarks": "Packaging directs to QR portal for manufacturer details; inspector did not complete portal verification."
        },
        "importer_details": {
            "is_imported": False,
            "country_of_origin": "India",
            "importer_name": None,
            "importer_address": None,
            "is_compliant": True,
            "compliance_remarks": "Domestic commodity."
        },
        "rule_13_quantity_audit": {
            "raw_quantity_text": "150 g",
            "declared_magnitude": 150.0,
            "declared_unit": "g",
            "is_rule_13_compliant": True,
            "rule_13_violations": []
        },
        "usp_cross_verification": {
            "mrp_numeric": 40.0,
            "quantity_numeric": 150.0,
            "quantity_unit": "g",
            "calculated_usp_per_base_unit": 0.27,
            "calculated_usp_unit": "Rs per g",
            "declared_usp_raw": "Rs. 0.27 per g",
            "declared_usp_numeric": 0.27,
            "is_mathematically_accurate": True,
            "discrepancy_amount": 0.0,
            "denomination_compliant": True,
            "is_compliant": True,
            "remarks": "USP matches calculated rate."
        },
        "second_schedule_shrinkflation_audit": {
            "is_second_schedule_commodity": False,
            "matched_commodity_category": None,
            "declared_quantity": "150.0 g",
            "is_standard_prescribed_pack_size": True,
            "prescribed_pack_sizes_sample": [],
            "nearest_standard_pack_size": None,
            "shrinkage_percentage": None,
            "is_compliant": True,
            "remarks": "Not on Second Schedule."
        },
        "visual_and_metrology_audit": {
            "rule_7_font_size": {
                "measured_numeral_height_mm": 2.5,
                "statutory_min_height_mm": 1.0,
                "status": "COMPLIANT",
                "is_compliant": True,
                "remarks": "Meets Table-I minimum."
            },
            "rule_9_color_contrast": {
                "contrast_ratio": "4.8:1",
                "is_compliant": True,
                "remarks": "Meets Rule 9(1)(b) threshold."
            }
        },
        "overall_compliance": "NEEDS_MANUAL_INSPECTION",
        "statutory_summary": [
            "Rule 6(1)(a) Incomplete Verification: Packaging directs to QR portal 'https://noice.in/suppliers' with batch code 'ZFF'. Portal verification was skipped by inspector; flagged for physical manual inspection."
        ]
    }

    rule_results, verdict, score, cross_refs = convert_master_report_to_rule_results(mock_master_report)

    # 1. Manufacturer rule must be marked as NEEDS_REVIEW (not hard FAIL)
    mfg_rule = next(r for r in rule_results if r["rule_id"] == "RULE_6_1_A")
    assert mfg_rule["status"] == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW, got {mfg_rule['status']}"
    assert mfg_rule["severity"] == "WARNING", f"Expected WARNING, got {mfg_rule['severity']}"
    assert "inspector did not complete portal verification" in mfg_rule["remarks"]

    # 2. Overall verdict must be FLAGGED_FOR_REVIEW (NEEDS_MANUAL_INSPECTION) rather than hard NON_COMPLIANT
    assert verdict in ["FLAGGED_FOR_REVIEW", "NEEDS_MANUAL_INSPECTION"]

def test_attended_qr_evidence_resolution():
    """
    Verify Step 4: When attended QR portal screenshot evidence is provided,
    manufacturer_details is populated with QR_PORTAL_ATTENDED and marks Rule 6(1)(a) PASS.
    """
    mock_master_report = {
        "product_name": "MASALA CHANA DAL",
        "total_images_analyzed": 1,
        "batch_number": "ZFF18G2628",
        "qr_code_detected_url": "https://noice.in/suppliers",
        "mandatory_declarations": {
            "generic_commodity_name": {"declared_value": "MASALA CHANA DAL", "compliance_status": "COMPLIANT", "is_compliant": True},
            "net_quantity": {"declared_value": "150 g", "compliance_status": "COMPLIANT", "is_compliant": True},
            "mrp": {"declared_value": "Rs. 40.00", "compliance_status": "COMPLIANT", "is_compliant": True},
            "unit_sale_price": {"declared_value": "Rs. 0.27 per g", "compliance_status": "COMPLIANT", "is_compliant": True},
            "mfg_or_pkd_date": {"declared_value": "12/25", "compliance_status": "COMPLIANT", "is_compliant": True},
            "consumer_care_details": {"declared_value": "care@example.com", "compliance_status": "COMPLIANT", "is_compliant": True},
            "country_of_origin": {"declared_value": "India", "compliance_status": "COMPLIANT", "is_compliant": True}
        },
        "manufacturer_details": {
            "resolution_method": "QR_PORTAL_ATTENDED",
            "resolved_manufacturer_name": "Noice Consumer Goods Pvt. Ltd.",
            "resolved_address": "Plot 42, Sector 8, IMT Manesar, Gurugram, Haryana 122050",
            "batch_code_used": "ZFF",
            "is_compliant": True,
            "compliance_remarks": "Manufacturer address successfully resolved via official QR portal using batch prefix 'ZFF'."
        },
        "importer_details": {"is_imported": False, "country_of_origin": "India", "is_compliant": True},
        "rule_13_quantity_audit": {"raw_quantity_text": "150 g", "declared_magnitude": 150.0, "declared_unit": "g", "is_rule_13_compliant": True, "rule_13_violations": []},
        "usp_cross_verification": {"is_compliant": True},
        "second_schedule_shrinkflation_audit": {"is_compliant": True},
        "visual_and_metrology_audit": {
            "rule_7_font_size": {"is_compliant": True, "measured_numeral_height_mm": 2.0},
            "rule_9_color_contrast": {"is_compliant": True, "contrast_ratio": "5.0:1"}
        },
        "overall_compliance": "COMPLIANT",
        "statutory_summary": ["All mandatory declarations comply strictly with LMR 2011."]
    }

    rule_results, verdict, score, cross_refs = convert_master_report_to_rule_results(mock_master_report)

    mfg_rule = next(r for r in rule_results if r["rule_id"] == "RULE_6_1_A")
    assert mfg_rule["status"] == "PASS"
    assert "Noice Consumer Goods" in mfg_rule["extracted_value"]
    assert "Haryana 122050" in mfg_rule["extracted_value"]
    assert mfg_rule["cross_referenced"] is True
    assert verdict == "COMPLIANT"
    assert score == 100.0

def test_validate_and_score_batch_code():
    """Verify batch code pattern detection against typical FMCG patterns and malformed tokens."""
    # Typical FMCG patterns -> high confidence
    assert validate_and_score_batch_code("02D42")[0] == "high"
    assert validate_and_score_batch_code("BP3 01H6^^")[0] == "high"
    assert validate_and_score_batch_code("09B11")[0] == "high"
    assert validate_and_score_batch_code("LOT 104B")[0] == "high"
    assert validate_and_score_batch_code("D42")[0] == "high"

    # Price tokens -> low confidence
    conf, flag = validate_and_score_batch_code("₹20.00")
    assert conf == "low"
    assert flag is not None and ("price" in flag.lower() or "usp" in flag.lower())

    conf, flag = validate_and_score_batch_code("Rs. 40")
    assert conf == "low"

    # Decimal weight / USP numbers (e.g. 2.9, 0.34) -> low confidence
    conf, flag = validate_and_score_batch_code("2.9")
    assert conf == "low"
    assert "decimal" in flag.lower() or "price" in flag.lower()

    # Dates (e.g. 01/26) -> low confidence
    conf, flag = validate_and_score_batch_code("01/26")
    assert conf == "low"
    assert "date" in flag.lower()

    # Empty / None -> low confidence
    conf, flag = validate_and_score_batch_code("")
    assert conf == "low"
    conf, flag = validate_and_score_batch_code(None)
    assert conf == "low"

def test_no_batch_code_on_package_resolution():
    """
    Verify that when packaging directs to a QR portal but no batch code is present on the package,
    the report is resolved with resolution_method: NO_BATCH_CODE_ON_PACKAGE,
    Rule 6(1)(a) status is NEEDS_REVIEW, and overall verdict is FLAGGED_FOR_REVIEW.
    """
    mock_master_report = {
        "product_name": "ITC BINGO MAD ANGLES",
        "total_images_analyzed": 1,
        "batch_number": "",
        "qr_code_detected_url": "https://bingosnacks.com/factory-locator.html?m=k",
        "mandatory_declarations": {
            "generic_commodity_name": {"declared_value": "MAD ANGLES", "compliance_status": "COMPLIANT", "is_compliant": True},
            "net_quantity": {"declared_value": "58 g", "compliance_status": "COMPLIANT", "is_compliant": True},
            "mrp": {"declared_value": "Rs. 20.00", "compliance_status": "COMPLIANT", "is_compliant": True},
            "unit_sale_price": {"declared_value": "Rs. 0.34 per g", "compliance_status": "COMPLIANT", "is_compliant": True},
            "mfg_or_pkd_date": {"declared_value": "01/26", "compliance_status": "COMPLIANT", "is_compliant": True},
            "consumer_care_details": {"declared_value": "itccares@itc.in", "compliance_status": "COMPLIANT", "is_compliant": True},
            "country_of_origin": {"declared_value": "India", "compliance_status": "COMPLIANT", "is_compliant": True}
        },
        "manufacturer_details": {
            "resolution_method": "NO_BATCH_CODE_ON_PACKAGE",
            "resolved_manufacturer_name": "UNRESOLVED - No Batch Code on Package",
            "resolved_address": "UNRESOLVED - No Batch Code on Package",
            "batch_code_used": None,
            "is_compliant": False,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "compliance_remarks": "Manufacturer portal verification required, but no batch code was found on the package to enter. Flagged for physical manual inspection."
        },
        "importer_details": {"is_imported": False, "country_of_origin": "India", "is_compliant": True},
        "rule_13_quantity_audit": {"raw_quantity_text": "58 g", "declared_magnitude": 58.0, "declared_unit": "g", "is_rule_13_compliant": True, "rule_13_violations": []},
        "usp_cross_verification": {"is_compliant": True},
        "second_schedule_shrinkflation_audit": {"is_compliant": True},
        "visual_and_metrology_audit": {
            "rule_7_font_size": {"is_compliant": True, "measured_numeral_height_mm": 2.0},
            "rule_9_color_contrast": {"is_compliant": True, "contrast_ratio": "5.0:1"}
        },
        "overall_compliance": "NEEDS_MANUAL_INSPECTION",
        "statutory_summary": [
            "Rule 6(1)(a) Needs Manual Inspection: Packaging directs to QR portal 'https://bingosnacks.com/factory-locator.html?m=k', but no batch code was found on the package to enter. Flagged for physical manual inspection."
        ]
    }

    rule_results, verdict, score, cross_refs = convert_master_report_to_rule_results(mock_master_report)

    mfg_rule = next(r for r in rule_results if r["rule_id"] == "RULE_6_1_A")
    assert mfg_rule["status"] == "NEEDS_REVIEW"
    assert mfg_rule["severity"] == "WARNING"
    assert "no batch code was found on the package" in mfg_rule["remarks"]
    assert verdict in ["FLAGGED_FOR_REVIEW", "NEEDS_MANUAL_INSPECTION"]

