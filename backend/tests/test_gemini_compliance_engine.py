import os
import pytest
from app.pipeline import rules_engine
from app.pipeline.visual_auditor import VisualAuditor
from app.pipeline.pipeline_manager import convert_master_report_to_rule_results

def test_statutory_penalties_framework():
    assert "SECTION_36_1" in rules_engine.STATUTORY_PENALTIES
    pen_36 = rules_engine.STATUTORY_PENALTIES["SECTION_36_1"]
    assert "25,000" in pen_36["first_offence_penalty"]
    assert "Section 36(1)" in pen_36["section"]

def test_unit_sale_price_mathematical_cross_verification():
    # Case 1: Exact calculation matches
    # MRP = Rs 38, Qty = 75g -> expected USP = 38 / 75 = 0.5067 Rs/g -> declared "Rs 0.51 per g"
    res1 = rules_engine.audit_unit_sale_price(
        mrp_val="₹ 38.00",
        quantity_magnitude=75.0,
        quantity_unit="g",
        declared_usp_str="₹ 0.51 per g"
    )
    assert res1["is_compliant"] is True
    assert res1["is_mathematically_accurate"] is True
    assert res1["discrepancy_amount"] == 0.0

    # Case 2: Inaccurate USP on pack
    # MRP = Rs 100, Qty = 200g -> expected USP = 0.50 Rs/g -> declared "Rs 0.85 per g" (35 paisa overcharge)
    res2 = rules_engine.audit_unit_sale_price(
        mrp_val="₹ 100.00",
        quantity_magnitude=200.0,
        quantity_unit="g",
        declared_usp_str="₹ 0.85 per g"
    )
    assert res2["is_compliant"] is False
    assert res2["is_mathematically_accurate"] is False
    assert len(res2["violations"]) > 0
    assert "Discrepancy" in res2["remarks"]

def test_second_schedule_anti_shrinkflation_audit():
    # Case 1: Standard pack size for Soaps (75g is permitted: 25, 50, 75, 100, 125, 150g)
    soap_res = rules_engine.audit_second_schedule_shrinkflation(
        product_name="Mysore Sandal Soap",
        generic_name="Toilet Soap",
        quantity_magnitude=75.0,
        quantity_unit="g"
    )
    assert soap_res["is_second_schedule_commodity"] is True
    assert soap_res["is_standard_prescribed_pack_size"] is True
    assert soap_res["is_compliant"] is True
    assert soap_res["shrinkage_percentage"] == 0.0

    # Case 2: Deceptive Shrinkflation pack size (e.g. 68g downsized soap)
    shrink_res = rules_engine.audit_second_schedule_shrinkflation(
        product_name="Brand X Bath Soap",
        generic_name="Toilet Soap",
        quantity_magnitude=68.0,
        quantity_unit="g"
    )
    assert shrink_res["is_second_schedule_commodity"] is True
    assert shrink_res["is_standard_prescribed_pack_size"] is False
    assert shrink_res["is_compliant"] is False
    assert shrink_res["shrinkage_percentage"] < 0  # Downsized vs 75g standard

def test_visual_metrology_font_height():
    # Package height = 140 mm, numeral height = 2.5% of 1000px = 25px -> 3.5 mm
    # For net quantity 100g, statutory min height is 1.0 mm (Rule 7 Table-I)
    font_res = VisualAuditor.audit_font_height(
        numeral_height_px=25,
        package_height_px=1000,
        actual_package_height_mm=140.0,
        quantity_magnitude=100.0,
        unit="g"
    )
    assert font_res["is_compliant"] is True
    assert font_res["measured_numeral_height_mm"] == 3.5
    assert font_res["statutory_min_height_mm"] == 1.0

def test_convert_master_report_girnar_tea_inspection():
    # Canonical Girnar tea instant premix report
    girnar_report = {
        "product_name": "GIRNAR CARDAMOM CHAI INSTANT TEA PREMIX",
        "total_images_analyzed": 1,
        "batch_number": "SEP. 2025",
        "mandatory_declarations": {
            "generic_commodity_name": {
                "declared_value": "CARDAMOM CHAI INSTANT TEA PREMIX",
                "found_on_panel": "Front Panel",
                "is_compliant": True,
                "compliance_remarks": "Generic name clearly declared."
            },
            "net_quantity": {
                "declared_value": "10 Sachets (Net Wt: 140g)",
                "found_on_panel": "Front Panel",
                "is_compliant": True,
                "compliance_remarks": "Standard SI unit g used."
            },
            "mrp": {
                "declared_value": "Rs. 135.00 (Incl. of all taxes)",
                "found_on_panel": "Side Panel",
                "is_compliant": True,
                "compliance_remarks": "Declared with mandatory inclusive of taxes."
            },
            "unit_sale_price": {
                "declared_value": "Rs. 13.50 per number",
                "found_on_panel": "Side Panel",
                "is_compliant": True,
                "compliance_remarks": "Declared accurately."
            },
            "mfg_or_pkd_date": {
                "declared_value": "SEP. 2025",
                "found_on_panel": "Side Panel",
                "is_compliant": True,
                "compliance_remarks": "Month and year clearly stated."
            },
            "consumer_care_details": {
                "declared_value": None,
                "found_on_panel": "NOT_FOUND",
                "is_compliant": False,
                "compliance_remarks": "Consumer care not found on scanned panel."
            },
            "country_of_origin": {
                "declared_value": "Product of India",
                "found_on_panel": "Side Panel",
                "is_compliant": True,
                "compliance_remarks": "Origin stated."
            }
        },
        "manufacturer_details": {
            "resolution_method": "ON_PACK",
            "resolved_manufacturer_name": "Girnar Food & Beverages Pvt. Ltd.",
            "resolved_address": "401, Centre Point, Dr. B. Ambedkar Marg, Parel, Mumbai 400012",
            "is_compliant": True,
            "compliance_remarks": "Full physical address declared on pack."
        },
        "rule_13_quantity_audit": {
            "declared_magnitude": 140,
            "declared_unit": "g",
            "is_rule_13_compliant": True,
            "rule_13_violations": []
        },
        "usp_cross_verification": {
            "mrp_numeric": 135.0,
            "quantity_numeric": 10,
            "quantity_unit": "number",
            "calculated_usp_per_base_unit": 13.5,
            "calculated_usp_unit": "Rs per number",
            "declared_usp_raw": "Rs. 13.50 per number",
            "is_compliant": True,
            "remarks": "Matches calculated Rs. 13.50 per number."
        },
        "second_schedule_shrinkflation_audit": {
            "is_second_schedule_commodity": False,
            "is_compliant": True,
            "remarks": "Not restricted."
        },
        "visual_and_metrology_audit": {
            "rule_7_font_size": {
                "measured_numeral_height_mm": 2.5,
                "statutory_min_height_mm": 1.0,
                "status": "COMPLIANT",
                "is_compliant": True
            },
            "rule_9_color_contrast": {
                "contrast_ratio": "4.5:1",
                "is_compliant": True
            }
        },
        "overall_compliance": "NON_COMPLIANT"
    }

    rules, verdict, score, cross_refs = convert_master_report_to_rule_results(girnar_report)
    assert verdict == "NON_COMPLIANT" # Correct because consumer care is missing!
    cc_rule = next(r for r in rules if r["rule_id"] == "RULE_6_1_F")
    assert cc_rule["status"] == "FAIL"
    mfg_rule = next(r for r in rules if r["rule_id"] == "RULE_6_1_A")
    assert mfg_rule["status"] == "PASS"
    assert "Girnar Food & Beverages" in mfg_rule["extracted_value"]

def test_convert_master_report_custard_powder_cross_panel():
    # Custard Powder multi-panel report: Back panel + Base panel cross-reference
    custard_report = {
        "product_name": "Crown Custard Powder",
        "total_images_analyzed": 2,
        "batch_number": "BNO: 042",
        "mandatory_declarations": {
            "generic_commodity_name": {
                "declared_value": "Custard Powder - Vanilla Flavour",
                "found_on_panel": "Panel 1",
                "is_compliant": True,
                "compliance_remarks": "Generic name declared."
            },
            "net_quantity": {
                "declared_value": "100 g",
                "found_on_panel": "Panel 2 (Base Panel)",
                "is_compliant": True,
                "compliance_remarks": "Declared on base panel pursuant to back panel cross-reference directive."
            },
            "mrp": {
                "declared_value": "₹ 45.00 (Incl. of all taxes)",
                "found_on_panel": "Panel 2 (Base Panel)",
                "is_compliant": True,
                "compliance_remarks": "MRP on base panel."
            },
            "unit_sale_price": {
                "declared_value": "₹ 0.45 per g",
                "found_on_panel": "Panel 2 (Base Panel)",
                "is_compliant": True,
                "compliance_remarks": "USP on base panel."
            },
            "mfg_or_pkd_date": {
                "declared_value": "PKD: 01/2026",
                "found_on_panel": "Panel 2 (Base Panel)",
                "is_compliant": True,
                "compliance_remarks": "PKD on base panel."
            },
            "consumer_care_details": {
                "declared_value": "Toll Free: 1800-102-2221, Email: care@crownfoods.com",
                "found_on_panel": "Panel 1",
                "is_compliant": True,
                "compliance_remarks": "Full contact details provided."
            },
            "country_of_origin": {
                "declared_value": "India",
                "found_on_panel": "Panel 1",
                "is_compliant": True,
                "compliance_remarks": "Made in India."
            }
        },
        "manufacturer_details": {
            "resolution_method": "ON_PACK",
            "resolved_manufacturer_name": "Crown Foods Pvt. Ltd.",
            "resolved_address": "Plot 18, Phase II, Peenya Industrial Area, Bengaluru - 560058, Karnataka",
            "is_compliant": True,
            "compliance_remarks": "Complete legal name and physical address declared on back panel."
        },
        "rule_13_quantity_audit": {
            "declared_magnitude": 100,
            "declared_unit": "g",
            "is_rule_13_compliant": True,
            "rule_13_violations": []
        },
        "usp_cross_verification": {
            "mrp_numeric": 45.0,
            "quantity_numeric": 100,
            "quantity_unit": "g",
            "calculated_usp_per_base_unit": 0.45,
            "calculated_usp_unit": "Rs per g",
            "declared_usp_raw": "₹ 0.45 per g",
            "is_compliant": True,
            "remarks": "Mathematically accurate."
        },
        "second_schedule_shrinkflation_audit": {
            "is_second_schedule_commodity": False,
            "is_compliant": True,
            "remarks": "Pack size compliant."
        },
        "visual_and_metrology_audit": {
            "rule_7_font_size": {
                "measured_numeral_height_mm": 3.2,
                "statutory_min_height_mm": 1.0,
                "status": "COMPLIANT",
                "is_compliant": True
            },
            "rule_9_color_contrast": {
                "contrast_ratio": "5.1:1",
                "is_compliant": True
            }
        },
        "overall_compliance": "COMPLIANT"
    }

    rules, verdict, score, cross_refs = convert_master_report_to_rule_results(custard_report)
    assert verdict == "COMPLIANT"
    assert score == 100.0
    # Net Qty, MRP, and PKD date are cross-referenced to Panel 2
    assert "net_quantity" in cross_refs
    assert "mrp" in cross_refs
    assert "mfg_or_pkd_date" in cross_refs
    # Ensure no raw text dumps
    for r in rules:
        assert len(r["extracted_value"]) < 200, f"Field {r['rule_id']} contains excessive dumped text!"
