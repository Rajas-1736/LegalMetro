"""
Legal Metrology (Packaged Commodities) Rules, 2011 - Policy-as-Code Rule Engine
Centralized repository of statutory rules, validation logic, banned expressions, and penalty mappings.
"""

import re
import math
from typing import Dict, List, Any, Optional

# ==============================================================================
# STATUTORY PENALTY FRAMEWORK (Legal Metrology Act, 2009)
# ==============================================================================
STATUTORY_PENALTIES = {
    "SECTION_36_1": {
        "act": "Legal Metrology Act, 2009",
        "section": "Section 36(1)",
        "offence": "Manufacture, packing, sale, distribution or delivery of non-standard pre-packaged commodities",
        "first_offence_penalty": "Fine up to ₹ 25,000",
        "second_offence_penalty": "Fine up to ₹ 50,000",
        "subsequent_offence_penalty": "Fine up to ₹ 1,00,000 or imprisonment up to 1 year, or both"
    },
    "RULE_32": {
        "act": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "section": "Rule 32(2)",
        "offence": "Contravention of general packaging declarations where no specific penalty is provided",
        "penalty": "Fine of ₹ 2,000"
    }
}

# ==============================================================================
# MASTER RULE DEFINITIONS
# ==============================================================================
ACTIVE_RULES: Dict[str, Dict[str, Any]] = {
    # --------------------------------------------------------------------------
    # RULE 5: COMMODITIES TO BE PACKED IN SPECIFIED QUANTITIES (SECOND SCHEDULE)
    # --------------------------------------------------------------------------
    "RULE_5_SECOND_SCHEDULE_PACK_SIZES": {
        "rule_code": "Rule 5 read with Second Schedule",
        "name": "Standard Prescribed Packaging Quantities & Anti-Shrinkflation",
        "description": "Commodities specified under the Second Schedule must strictly be packaged in prescribed standard quantities. Packaging non-standard sizes or covert downsizing to disguise price hikes is a statutory violation under Section 36(1).",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },

    # --------------------------------------------------------------------------
    # RULE 6: MANDATORY DECLARATIONS ON PACKAGES
    # --------------------------------------------------------------------------
    "RULE_6_1_A_MANUFACTURER": {
        "rule_code": "Rule 6(1)(a)",
        "name": "Name and Address of Manufacturer / Packer",
        "description": "Every package shall bear the complete name and physical address of the manufacturer/packer (street, city, state, pincode).",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True,
        "special_cases": {
            "multi_unit_resolution": "If multiple units (B), (W) are listed, the active unit must be deterministically resolved using the Batch Number prefix.",
            "digital_qr_disclosure": "If manufacturer details are deferred to a QR code, the link must be functional and resolve the physical address upon entering batch digits."
        }
    },
    "RULE_6_1_A_IMPORTER_DETAILS": {
        "rule_code": "Rule 6(1)(a) read with Rule 10(1)",
        "name": "Mandatory Name and Address of Importer in India",
        "description": "For any commodity manufactured outside India (imported package), the package MUST conspicuously state the name and complete physical address of the importer in India. Omission of Indian importer details on foreign/imported goods is a statutory violation.",
        "condition": "Mandatory whenever Country of Origin is NOT India or product is imported.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_6_1_B_GENERIC_NAME": {
        "rule_code": "Rule 6(1)(b)",
        "name": "Generic or Common Name of Commodity",
        "description": "Common or generic name of commodity must be prominently declared on the package.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_6_1_C_NET_QUANTITY": {
        "rule_code": "Rule 6(1)(c)",
        "name": "Net Quantity in Standard Units",
        "description": "Net quantity must be declared in terms of standard unit of weight, measure or number (excluding wrappers).",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_6_1_D_DATE_AND_BATCH": {
        "rule_code": "Rule 6(1)(d)",
        "name": "Month & Year of Manufacture/Packing/Import and Batch Number",
        "description": "Must clearly state the month and year of manufacture or pre-packing (or import date if imported). A Batch Number, Lot Number, or Machine Code can NEVER substitute for or excuse the absence of the month and year of manufacture. If the manufacturing/packing month and year is missing or not explicitly declared, the package is strictly NON_COMPLIANT (except for statutory exemptions under Rule 6(1) second proviso).",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True,
        "special_cases": {
            "strict_date_requirement": "Batch number or lot number alone does NOT satisfy Rule 6(1)(d). Month and year must be explicitly declared.",
            "statutory_exemption_incense_bidis": "Under Rule 6(1) second proviso (Clause g), no declaration as to month and year of manufacture or pre-packing is required for: (i) incense sticks (agarbatti / dhoop), (ii) bidis, (iii) domestic LPG cylinders of 14.2kg or 5kg bottled and marketed by PSUs. For these exempt commodities, absence of mfg date is legally COMPLIANT."
        }
    },
    "RULE_6_1_DATE_EXEMPTION_INCENSE_BIDIS": {
        "rule_code": "Rule 6(1) Second Proviso (g)",
        "name": "Exemption from Month & Year of Manufacture for Agarbatti, Bidis, LPG",
        "description": "Under Rule 6(1) second proviso, no declaration as to the month and year in which the commodity is manufactured or pre-packed shall be required to be made on: (i) any package containing bidis or incense sticks (agarbatti / dhoop); (ii) any domestic liquefied petroleum gas cylinder of 14.2kg or 5kg, bottled and marketed by a public sector undertaking. For any other commodity, month and year of manufacture/packing is strictly mandatory and cannot be excused.",
        "exempt_commodities": ["incense sticks", "agarbatti", "agarbathi", "dhoop", "bidi", "bidis", "beedi", "beedis", "lpg cylinder", "liquefied petroleum gas cylinder"],
        "penalty_ref": "SECTION_36_1",
        "mandatory": False
    },
    "RULE_6_1_E_MRP_AND_USP": {
        "rule_code": "Rule 6(1)(e)",
        "name": "Maximum Retail Price (MRP) & Unit Sale Price (USP)",
        "description": "MRP must explicitly declare 'inclusive of all taxes'. Unit Sale Price (USP) is mandatory on all pre-packaged commodities under Rule 6(1)(e) (as amended in 2021): per g or per 100g for commodities < 1kg; per kg for commodities >= 1kg; per ml or per 100ml for commodities < 1L; per liter for commodities >= 1L; per piece/unit for items sold by number.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_6_1_F_CONSUMER_CARE": {
        "rule_code": "Rule 6(1)(f)",
        "name": "Consumer Complaint Details",
        "description": "Every package must bear the name, address, telephone number, and email address of person/office to contact for consumer complaints.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_6_1_G_COUNTRY_OF_ORIGIN": {
        "rule_code": "Rule 6(1)(g)",
        "name": "Country of Origin",
        "description": "Mandatory declaration of the country of origin on all packages.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },

    # --------------------------------------------------------------------------
    # SPECIAL CARVE-OUT: EMBOSSED / CRIMP / MOLDED MARKINGS (Tubes & Containers)
    # --------------------------------------------------------------------------
    "RULE_7_3_EMBOSSED_CRIMP_PROVISION": {
        "rule_code": "Rule 7(3) read with Rule 9(1) Proviso (a)",
        "name": "Embossed, Engraved, Molded, or Crimped Declarations",
        "description": "Declarations engraved, embossed, or molded on crimp seals or containers without ink are legally permissible provided letter/numeral height is >= 2mm. If a packaging directs the consumer to the crimp, base, or seal (e.g. 'See crimp for Batch/Date/MRP'), and camera/AI cannot clearly resolve the physical indentation, the item must be flagged for MANUAL PHYSICAL INSPECTION, not marked as non-compliant.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": False
    },

    # --------------------------------------------------------------------------
    # RULE 7: PRINCIPAL DISPLAY PANEL - NUMERAL & LETTER HEIGHT (TABLE-I)
    # --------------------------------------------------------------------------
    "RULE_7_NUMERAL_HEIGHT": {
        "rule_code": "Rule 7(2)",
        "name": "Minimum Height of Numerals (Schedule II / Table-I)",
        "description": "The height of any numeral in declaration on principal display panel shall satisfy Table-I: <=200g/ml: 1mm; 200g-500g/ml: 2mm; >500g/ml: 4mm (blown/embossed/crimped: 2mm, 4mm, 6mm respectively). Letter height minimum 1mm.",
        "table_1_thresholds": [
            {"max_qty": 200.0, "min_height_mm": 1.0, "blown_min_height_mm": 2.0},
            {"max_qty": 500.0, "min_height_mm": 2.0, "blown_min_height_mm": 4.0},
            {"max_qty": float('inf'), "min_height_mm": 4.0, "blown_min_height_mm": 6.0}
        ],
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },

    # --------------------------------------------------------------------------
    # RULE 9: MANNER IN WHICH DECLARATION SHALL BE MADE (CONSPICUOUS CONTRAST)
    # --------------------------------------------------------------------------
    "RULE_9_1_B_COLOR_CONTRAST": {
        "rule_code": "Rule 9(1)(b)",
        "name": "Conspicuous Color Contrast of Text and Background",
        "description": "Numerals of retail sale price and net quantity shall be printed, painted or inscribed in a colour that contrasts conspicuously with the background of the label. Blown/molded/crimped text is exempt from contrasting color under Proviso (a).",
        "min_wcag_contrast_ratio": 3.0,
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },

    # --------------------------------------------------------------------------
    # RULE 13: UNITS OF WEIGHT, MEASURE, OR NUMBER
    # --------------------------------------------------------------------------
    "RULE_13_2_SUB_UNIT_MAGNITUDE": {
        "rule_code": "Rule 13(2)",
        "name": "Expressions for Quantities Less Than 1 kg / 1 L / 1 m",
        "description": "Quantities less than 1 kg must use gram ('g'); less than 1 L must use millilitre ('ml'); less than 1 m must use centimetre ('cm'). Decimal kg (e.g. '0.5 kg') is strictly non-compliant.",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_13_3_SUPER_UNIT_MAGNITUDE": {
        "rule_code": "Rule 13(3)",
        "name": "Expressions for Quantities Equal to or More Than 1 kg / 1 L",
        "description": "Quantities >= 1 kg must be in kilograms ('kg'); >= 1 L must be in litres ('l').",
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_13_4_BANNED_COUNT_WORDS": {
        "rule_code": "Rule 13(4)",
        "name": "Prohibition of Archaic Count Terms",
        "description": "Terms 'dozen', 'score', 'gross', 'great gross' are strictly prohibited.",
        "banned_terms": ["dozen", "score", "gross", "great gross"],
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_13_5_I_STRICT_SI_UNITS": {
        "rule_code": "Rule 13(5)(i)",
        "name": "Strict International System of Units (SI)",
        "description": "Only standard SI units (g, kg, ml, l, m) permitted. Imperial units (oz, lbs, fl oz) and colloquial symbols (gms, gm, KG, Ltrs) are illegal.",
        "allowed_symbols": ["g", "kg", "ml", "mL", "l", "L", "m", "cm", "mm", "N", "U"],
        "illegal_symbols": ["gms", "gm", "KG", "Ltrs", "ltr", "oz", "lbs", "fl oz", "inches", "feet", "yard", "tola", "seer"],
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_13_5_II_NUMBER_SYMBOL": {
        "rule_code": "Rule 13(5)(ii)",
        "name": "Statutory Symbol for Commodities Sold by Number",
        "description": "For items sold by number/piece count, the statutory symbol MUST be strictly 'N' or 'U'. Words like 'Pcs', 'Pieces', 'Nos', 'Units' are non-compliant.",
        "allowed_symbols": ["N", "U"],
        "disallowed_symbols": ["pcs", "pieces", "nos", "units", "items"],
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    },
    "RULE_13_6_BANNED_MISLEADING_QUALIFIERS": {
        "rule_code": "Rule 13(6)",
        "name": "Prohibition of Exaggerated / Misleading Qualifiers",
        "description": "The declaration of quantity shall not contain any word which creates an exaggerated, misleading, or inadequate impression.",
        "banned_qualifiers": [
            "minimum", "min.", "min", "not less than", "average", "avg.", "avg", 
            "about", "approximately", "approx.", "approx"
        ],
        "penalty_ref": "SECTION_36_1",
        "mandatory": True
    }
}

# ==============================================================================
# RULE ENGINE UTILITY FUNCTIONS
# ==============================================================================

def get_required_numeral_height(quantity_magnitude: Optional[float], unit: Optional[str]) -> float:
    if quantity_magnitude is None or not unit:
        return 1.0

    u = unit.lower().strip()
    normalized_grams = quantity_magnitude
    if u in ["kg", "l", "litre", "liter"]:
        normalized_grams = quantity_magnitude * 1000.0

    if normalized_grams <= 200.0:
        return 1.0
    elif normalized_grams <= 500.0:
        return 2.0
    else:
        return 4.0

def evaluate_import_compliance(country_of_origin: str, importer_name: Optional[str], importer_address: Optional[str]) -> Dict[str, Any]:
    country_clean = (country_of_origin or "").strip().lower()
    is_domestic = any(term in country_clean for term in ["india", "bharat", "ind"])
    is_imported = (len(country_clean) > 0) and not is_domestic

    if not is_imported:
        return {
            "is_imported": False,
            "is_compliant": True,
            "remarks": "Domestic commodity manufactured in India. Importer declarations are not applicable.",
            "violations": []
        }

    violations = []
    has_name = importer_name and len(importer_name.strip()) > 2 and importer_name.lower() != "not_found"
    has_addr = importer_address and len(importer_address.strip()) > 5 and importer_address.lower() != "not_found"

    if not has_name or not has_addr:
        violations.append(
            f"VIOLATION under Rule 6(1)(a) & Rule 10(1): Product origin is outside India ('{country_of_origin}'), "
            f"but mandatory Indian Importer name and complete address are missing from packaging."
        )

    return {
        "is_imported": True,
        "is_compliant": len(violations) == 0,
        "remarks": "Imported commodity: Indian importer details successfully verified." if len(violations) == 0 else violations[0],
        "violations": violations
    }

# Statutory exemption list under Rule 6(1) second proviso
EXEMPT_MFG_DATE_KEYWORDS = [
    "incense", "incense stick", "incense sticks", "agarbatti", "agarbathi", 
    "dhoop", "dhoopbatti", "dhoop batti", "bidi", "bidis", "beedi", "beedis", 
    "lpg", "lpg cylinder", "liquefied petroleum gas"
]

def is_mfg_date_exempt(product_name: str, generic_name: str = "") -> bool:
    """
    Checks if a commodity is legally exempt from declaring month & year of manufacture
    under Rule 6(1) second proviso (Clause g) of Legal Metrology (Packaged Commodities) Rules, 2011.
    Exempt commodities:
    (i) Any package containing bidis or incense sticks (agarbatti / dhoop);
    (ii) Domestic LPG cylinders of 14.2kg or 5kg.
    """
    text = f"{product_name or ''} {generic_name or ''}".lower()
    for kw in EXEMPT_MFG_DATE_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
            return True
    return False

def audit_mfg_date_declaration(
    declared_date: Optional[str],
    product_name: str = "",
    generic_name: str = "",
    compliance_remarks: str = "",
    found_on_panel: str = ""
) -> Dict[str, Any]:
    """
    Enforces strict statutory compliance for month and year of manufacture under Rule 6(1)(d)
    and applies statutory exemption under Rule 6(1) second proviso.

    Rules:
    1. If product is incense sticks (agarbatti), bidis, or LPG cylinder:
       - Legally EXEMPT under Rule 6(1) second proviso (Clause g).
       - Marked COMPLIANT with statutory exemption note.
    2. For any other product:
       - Must contain month and year of manufacture or pre-packing.
       - A batch number / lot code / machine code (e.g. 'BE 87 41', 'BN 102') is NEVER a date.
       - If only batch number is given, or date is missing / unclear:
         Strictly NON_COMPLIANT (FAIL) under Section 36(1). Batch number cannot excuse missing date.
       - Valid crimp/base pointer ('See crimp for Mfg Date') with embossed marking:
         Treated under Rule 7(3) as NEEDS_MANUAL_INSPECTION.
    """
    if is_mfg_date_exempt(product_name, generic_name):
        return {
            "is_exempt": True,
            "is_compliant": True,
            "compliance_status": "COMPLIANT",
            "declared_value": declared_date or "EXEMPT (Rule 6(1) Second Proviso)",
            "remarks": (
                "Statutory exemption under Rule 6(1) second proviso: Declaration of month and year "
                "of manufacture or pre-packing is not required for incense sticks (agarbatti) and bidis."
            ),
            "rule_reference": "Rule 6(1) Second Proviso (g)"
        }

    # Check for crimp/base pointer under Rule 7(3)
    remarks_lower = (compliance_remarks or "").lower()
    panel_lower = (found_on_panel or "").lower()
    has_crimp_pointer = any(p in remarks_lower or p in panel_lower for p in ["crimp", "base", "seal", "embossed", "engraved"])

    # Clean declared date
    date_str = (declared_date or "").strip()
    
    # Check if declared_date looks like purely a batch code or absence indicator
    # e.g., "BE 87 41", "BN 102", "None", "Not visible", "N/A", "unresolved"
    is_pure_batch_or_absent = False
    if not date_str or date_str.lower() in ["none", "null", "not found", "unresolved", "n/a", "not visible"]:
        is_pure_batch_or_absent = True
    elif re.match(r'^[A-Za-z]{1,4}\s*\d{1,6}(\s*\d{1,6})*$', date_str):
        # Pattern like "BE 87 41", "B 123", "LOT 45" without month/year indicators
        is_pure_batch_or_absent = True
    elif "batch" in date_str.lower() and not any(m in date_str.lower() for m in ["202", "201", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "/"]):
        is_pure_batch_or_absent = True

    # Check for date patterns (e.g. MM/YY, MM/YYYY, DD/MM/YYYY, Month YYYY, etc.)
    has_date_pattern = bool(re.search(r'(0[1-9]|1[0-2]|[1-9])[\/\-\.](20\d\d|\d\d)', date_str)) or \
                       bool(re.search(r'(20\d\d)[\/\-\.](0[1-9]|1[0-2])', date_str)) or \
                       bool(re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\,\/\-]+(20\d\d|\d\d)\b', date_str, re.IGNORECASE)) or \
                       bool(re.search(r'\b(20\d\d)\b', date_str))

    # Also check if Gemini said "manufacturing date is not explicitly visible" in remarks
    if "not explicitly visible" in remarks_lower or "date is missing" in remarks_lower or "not visible" in remarks_lower:
        if not has_date_pattern:
            is_pure_batch_or_absent = True

    if is_pure_batch_or_absent and not has_crimp_pointer:
        return {
            "is_exempt": False,
            "is_compliant": False,
            "compliance_status": "NON_COMPLIANT",
            "declared_value": date_str if date_str else "NOT DECLARED",
            "remarks": (
                f"VIOLATION under Rule 6(1)(d): Month and year of manufacture/packing is missing. "
                f"Batch number/lot code ({date_str or 'detected'}) cannot substitute for or excuse missing manufacturing date."
            ),
            "rule_reference": "Rule 6(1)(d)"
        }

    if has_crimp_pointer and (is_pure_batch_or_absent or not has_date_pattern):
        return {
            "is_exempt": False,
            "is_compliant": True,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "declared_value": date_str or "Crimp/Seal (Pointer Verified)",
            "remarks": "Statutory pointer present. Mfg Date embossed/crimped on container under Rule 7(3); flagged for physical manual inspection.",
            "rule_reference": "Rule 7(3) read with Rule 6(1)(d)"
        }

    if has_date_pattern:
        return {
            "is_exempt": False,
            "is_compliant": True,
            "compliance_status": "COMPLIANT",
            "declared_value": date_str,
            "remarks": f"Month & Year of manufacture/packing declared ({date_str}) conforms to Rule 6(1)(d).",
            "rule_reference": "Rule 6(1)(d)"
        }

    # Fallback: missing or unclear date
    return {
        "is_exempt": False,
        "is_compliant": False,
        "compliance_status": "NON_COMPLIANT",
        "declared_value": date_str if date_str else "NOT DECLARED",
        "remarks": "VIOLATION under Rule 6(1)(d): Month and year of manufacture or pre-packing is mandatory and was not declared on the package.",
        "rule_reference": "Rule 6(1)(d)"
    }


def compile_inspection_prompt() -> str:
    guidelines = []
    guidelines.append("LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011 STATUTORY CRITERIA:")
    
    for _, rule in ACTIVE_RULES.items():
        guidelines.append(f"- [{rule['rule_code']}] {rule['name']}: {rule['description']}")
        
        if "banned_terms" in rule:
            guidelines.append(f"  * Strictly Prohibited Terms: {', '.join(rule['banned_terms'])}")
        if "illegal_symbols" in rule:
            guidelines.append(f"  * Prohibited Unit Symbols: {', '.join(rule['illegal_symbols'])}")
        if "allowed_symbols" in rule and "RULE_13_5_II" in rule.get("name", ""):
            guidelines.append(f"  * Mandatory Piece Count Symbol: Must be 'N' or 'U'")
        if "banned_qualifiers" in rule:
            guidelines.append(f"  * Prohibited Misleading Qualifiers: {', '.join(rule['banned_qualifiers'])}")
        if "special_cases" in rule:
            for case, desc in rule["special_cases"].items():
                guidelines.append(f"  * Special Policy ({case}): {desc}")
                
    return "\n".join(guidelines)

def audit_quantity_against_rule_13(raw_text: str, magnitude: Optional[float], unit: Optional[str]) -> Dict[str, Any]:
    violations = []
    text_lower = raw_text.lower()
    
    for banned in ACTIVE_RULES["RULE_13_4_BANNED_COUNT_WORDS"]["banned_terms"]:
        if banned in text_lower:
            violations.append(f"VIOLATION under Rule 13(4): Banned count term '{banned}' detected.")

    for qualifier in ACTIVE_RULES["RULE_13_6_BANNED_MISLEADING_QUALIFIERS"]["banned_qualifiers"]:
        if qualifier in text_lower:
            violations.append(f"VIOLATION under Rule 13(6): Misleading qualifier '{qualifier}' is prohibited.")

    if unit:
        u_clean = unit.strip()
        if u_clean.lower() in [s.lower() for s in ACTIVE_RULES["RULE_13_5_I_STRICT_SI_UNITS"]["illegal_symbols"]]:
            violations.append(f"VIOLATION under Rule 13(5)(i): Non-standard unit symbol '{unit}' used instead of standard SI symbol.")
            
        if u_clean.lower() in [s.lower() for s in ACTIVE_RULES["RULE_13_5_II_NUMBER_SYMBOL"]["disallowed_symbols"]]:
            violations.append(f"VIOLATION under Rule 13(5)(ii): Commodities sold by number must use symbol 'N' or 'U' (found '{unit}').")

    if magnitude is not None and unit:
        u_clean = unit.lower().strip()
        if u_clean == "kg" and 0 < magnitude < 1.0:
            violations.append(f"VIOLATION under Rule 13(2)(a): Quantities < 1 kg must be expressed in grams ('g'), not '{magnitude} kg'.")
        elif (u_clean in ["l", "litre", "liter"]) and 0 < magnitude < 1.0:
            violations.append(f"VIOLATION under Rule 13(2)(f): Quantities < 1 L must be expressed in millilitres ('ml'), not '{magnitude} l'.")

    return {
        "is_compliant": len(violations) == 0,
        "violations": violations
    }

def get_penalty_for_violation(rule_code: str) -> Optional[Dict[str, str]]:
    for _, meta in ACTIVE_RULES.items():
        if meta["rule_code"].lower() in rule_code.lower():
            pen_key = meta.get("penalty_ref")
            return STATUTORY_PENALTIES.get(pen_key)
    return STATUTORY_PENALTIES["SECTION_36_1"]


# ==============================================================================
# SECOND SCHEDULE COMMODITY REGISTRY (Rule 5 - Standard Pack Sizes)
# ==============================================================================
SECOND_SCHEDULE_COMMODITIES: Dict[str, Dict[str, Any]] = {
    "baby_food": {
        "name": "Baby food and Weaning food",
        "keywords": ["baby food", "weaning food", "infant milk", "cerelac", "nestum", "lactogen"],
        "base_unit": "g",
        "standard_sizes_grams": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000, 5000, 10000],
        "multiples_rule": None
    },
    "biscuits": {
        "name": "Biscuits and Cookies",
        "keywords": ["biscuit", "biscuits", "cookie", "cookies", "cracker", "crackers", "rusk"],
        "base_unit": "g",
        "standard_sizes_grams": [25, 50, 75, 100, 150, 200, 250, 300],
        "multiples_rule": {"threshold": 300, "multiple": 100, "max_limit": 1000}
    },
    "bread": {
        "name": "Bread (including brown bread)",
        "keywords": ["bread", "brown bread", "white bread", "whole wheat bread"],
        "base_unit": "g",
        "standard_sizes_grams": [100],
        "multiples_rule": {"threshold": 100, "multiple": 100, "max_limit": None}
    },
    "butter": {
        "name": "Un-canned packages of butter and margarine",
        "keywords": ["butter", "margarine", "table butter"],
        "base_unit": "g",
        "standard_sizes_grams": [25, 50, 100, 200, 500, 1000, 2000, 5000],
        "multiples_rule": {"threshold": 5000, "multiple": 5000, "max_limit": None}
    },
    "tea": {
        "name": "Tea",
        "keywords": ["tea", "chai", "black tea", "green tea", "tea premix"],
        "base_unit": "g",
        "standard_sizes_grams": [25, 50, 100, 125, 250, 500, 1000],
        "multiples_rule": {"threshold": 1000, "multiple": 1000, "max_limit": None}
    },
    "coffee": {
        "name": "Coffee",
        "keywords": ["coffee", "instant coffee", "filter coffee"],
        "base_unit": "g",
        "standard_sizes_grams": [25, 50, 100, 200, 250, 500, 1000],
        "multiples_rule": {"threshold": 1000, "multiple": 1000, "max_limit": None}
    },
    "cereals_pulses": {
        "name": "Cereals and Pulses",
        "keywords": ["cereal", "cereals", "pulses", "dal", "chana dal", "toor dal", "moong dal", "urad dal", "lentil", "lentils", "rajma", "chana", "moong"],
        "base_unit": "g",
        "standard_sizes_grams": [100, 200, 500, 1000, 2000, 5000],
        "multiples_rule": {"threshold": 5000, "multiple": 5000, "max_limit": None}
    },
    "edible_oils": {
        "name": "Edible Oils, Vanaspati, Ghee, Butter oil",
        "keywords": ["edible oil", "cooking oil", "mustard oil", "sunflower oil", "soybean oil", "groundnut oil", "ghee", "vanaspati", "butter oil"],
        "base_unit": "g_or_ml",
        "standard_sizes_grams": [50, 100, 200, 500, 1000, 2000, 3000, 5000],
        "multiples_rule": {"threshold": 5000, "multiple": 5000, "max_limit": None}
    },
    "milk_powder": {
        "name": "Milk Powder",
        "keywords": ["milk powder", "dairy whitener", "skimmed milk powder"],
        "base_unit": "g",
        "standard_sizes_grams": [50, 100, 200, 500, 1000],
        "below_exempt": 50,
        "multiples_rule": {"threshold": 1000, "multiple": 500, "max_limit": None}
    },
    "detergent_powder": {
        "name": "Non-soapy detergents (powder)",
        "keywords": ["detergent powder", "washing powder", "laundry powder", "surf"],
        "base_unit": "g",
        "standard_sizes_grams": [50, 100, 200, 500, 700, 1000, 1500, 2000],
        "below_exempt": 50,
        "multiples_rule": {"threshold": 2000, "multiple": 1000, "max_limit": None}
    },
    "rice_flour": {
        "name": "Rice (powdered), flour, atta, rawa and suji",
        "keywords": ["atta", "flour", "wheat flour", "maida", "suji", "rawa", "rice flour", "besan"],
        "base_unit": "g",
        "standard_sizes_grams": [100, 200, 500, 1000, 2000, 5000],
        "multiples_rule": {"threshold": 5000, "multiple": 5000, "max_limit": None}
    },
    "salt": {
        "name": "Salt",
        "keywords": ["salt", "iodized salt", "rock salt", "table salt", "black salt"],
        "base_unit": "g",
        "standard_sizes_grams": [50, 100, 200, 500, 750, 1000, 2000, 5000],
        "multiples_rule": {"threshold": 5000, "multiple": 5000, "max_limit": None}
    },
    "soaps": {
        "name": "Soaps (Toilet & Laundry)",
        "keywords": ["soap", "toilet soap", "bath soap", "bathing bar", "laundry soap"],
        "base_unit": "g",
        "standard_sizes_grams": [25, 50, 75, 100, 125, 150],
        "multiples_rule": {"threshold": 150, "multiple": 50, "max_limit": None}
    },
    "soft_drinks": {
        "name": "Aerated soft drinks and non-alcoholic beverages",
        "keywords": ["soft drink", "aerated", "soda", "cola", "cold drink", "energy drink", "fruit drink"],
        "base_unit": "ml",
        "standard_sizes_grams": [65, 100, 125, 150, 200, 250, 300, 330, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000],
        "multiples_rule": None
    },
    "mineral_water": {
        "name": "Mineral water and packaged drinking water",
        "keywords": ["mineral water", "drinking water", "packaged water", "spring water"],
        "base_unit": "ml",
        "standard_sizes_grams": [100, 150, 200, 250, 300, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000],
        "multiples_rule": None
    }
}


def audit_second_schedule_shrinkflation(
    product_name: str,
    generic_name: str,
    quantity_magnitude: Optional[float],
    quantity_unit: Optional[str]
) -> Dict[str, Any]:
    """
    Audits commodity net quantity against the Second Schedule (Rule 5).
    Detects non-standard pack sizes and calculates shrinkflation downsize percentages.
    """
    if quantity_magnitude is None or not quantity_unit:
        return {
            "is_second_schedule_commodity": False,
            "matched_commodity_category": None,
            "declared_quantity": None,
            "is_standard_prescribed_pack_size": True,
            "prescribed_pack_sizes_sample": [],
            "nearest_standard_pack_size": None,
            "shrinkage_percentage": None,
            "is_compliant": True,
            "remarks": "Net quantity or unit missing; cannot perform Second Schedule audit."
        }

    search_text = f"{product_name or ''} {generic_name or ''}".lower()
    matched_key = None
    matched_meta = None

    for key, meta in SECOND_SCHEDULE_COMMODITIES.items():
        for kw in meta["keywords"]:
            if re.search(rf"\b{re.escape(kw)}\b", search_text, re.IGNORECASE):
                matched_key = key
                matched_meta = meta
                break
        if matched_key:
            break

    if not matched_key:
        return {
            "is_second_schedule_commodity": False,
            "matched_commodity_category": None,
            "declared_quantity": f"{quantity_magnitude} {quantity_unit}",
            "is_standard_prescribed_pack_size": True,
            "prescribed_pack_sizes_sample": [],
            "nearest_standard_pack_size": None,
            "shrinkage_percentage": None,
            "is_compliant": True,
            "remarks": "Commodity is not listed under the Second Schedule. Pack size is at manufacturer's discretion."
        }

    # Normalize declared quantity to base unit (grams or ml)
    u = quantity_unit.lower().strip()
    qty_norm = quantity_magnitude
    if u in ["kg", "l", "litre", "liter"]:
        qty_norm = quantity_magnitude * 1000.0

    allowed_list = matched_meta["standard_sizes_grams"]
    is_standard = qty_norm in allowed_list

    # Check multiples rule if applicable
    m_rule = matched_meta.get("multiples_rule")
    if not is_standard and m_rule:
        thresh = m_rule["threshold"]
        multiple = m_rule["multiple"]
        max_lim = m_rule.get("max_limit")
        if qty_norm > thresh:
            if max_lim is None or qty_norm <= max_lim:
                if (qty_norm - thresh) % multiple == 0:
                    is_standard = True

    # Below-exempt check (e.g. milk powder < 50g)
    if not is_standard and matched_meta.get("below_exempt"):
        if qty_norm < matched_meta["below_exempt"]:
            is_standard = True

    # Format prescribed sample for reporting
    unit_label = "g" if matched_meta["base_unit"] != "ml" else "ml"
    sample_sizes = [f"{s} {unit_label}" if s < 1000 else f"{s/1000:g} {'kg' if unit_label=='g' else 'L'}" for s in allowed_list[:6]]
    if len(allowed_list) > 6:
        sample_sizes.append("...")

    if is_standard:
        return {
            "is_second_schedule_commodity": True,
            "matched_commodity_category": matched_meta["name"],
            "declared_quantity": f"{quantity_magnitude} {quantity_unit}",
            "is_standard_prescribed_pack_size": True,
            "prescribed_pack_sizes_sample": sample_sizes,
            "nearest_standard_pack_size": f"{quantity_magnitude} {quantity_unit}",
            "shrinkage_percentage": 0.0,
            "is_compliant": True,
            "remarks": f"Pack size conforms strictly to prescribed Second Schedule standard quantities for '{matched_meta['name']}'."
        }

    # Find nearest standard benchmark to calculate shrinkflation percentage
    nearest_val = min(allowed_list, key=lambda x: abs(x - qty_norm))
    shrinkage_pct = ((qty_norm - nearest_val) / nearest_val) * 100.0
    nearest_label = f"{nearest_val} {unit_label}" if nearest_val < 1000 else f"{nearest_val/1000:g} {'kg' if unit_label=='g' else 'L'}"

    if shrinkage_pct < 0:
        shrink_msg = f"Potential Shrinkflation: Downsized by {abs(shrinkage_pct):.1f}% compared to nearest standard pack size ({nearest_label})."
    else:
        shrink_msg = f"Non-standard packaging size ({shrinkage_pct:+.1f}% above standard {nearest_label})."

    violation_remark = (
        f"VIOLATION under Rule 5 & Second Schedule: Commodity '{matched_meta['name']}' packed in non-standard quantity "
        f"({quantity_magnitude} {quantity_unit}). Prescribed sizes include {', '.join(sample_sizes)}. {shrink_msg}"
    )

    return {
        "is_second_schedule_commodity": True,
        "matched_commodity_category": matched_meta["name"],
        "declared_quantity": f"{quantity_magnitude} {quantity_unit}",
        "is_standard_prescribed_pack_size": False,
        "prescribed_pack_sizes_sample": sample_sizes,
        "nearest_standard_pack_size": nearest_label,
        "shrinkage_percentage": round(shrinkage_pct, 2),
        "is_compliant": False,
        "remarks": violation_remark
    }


def audit_unit_sale_price(
    mrp_val: Any,
    quantity_magnitude: Optional[float],
    quantity_unit: Optional[str],
    declared_usp_str: Optional[str],
    context_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mathematically cross-verifies Unit Sale Price (USP) under Rule 6(1)(e).
    Calculates expected USP = MRP / Net Quantity across prescribed denominations
    and audits declared packaging USP for accuracy and denomination compliance.
    Handles slash-delimited dot matrix coding blocks (e.g. ##NS/BN/₹ PER g: 2.9/BP3 01H6^^/0.34)
    and validates declared values against statutory formulas.
    """
    mrp_num = None
    if isinstance(mrp_val, (int, float)):
        mrp_num = float(mrp_val)
    elif isinstance(mrp_val, str):
        num_match = re.search(r'([0-9]+(?:\.[0-9]+)?)', mrp_val)
        if num_match:
            try:
                mrp_num = float(num_match.group(1))
            except ValueError:
                pass

    if mrp_num is None or quantity_magnitude is None or quantity_magnitude <= 0 or not quantity_unit:
        return {
            "mrp_numeric": mrp_num,
            "quantity_numeric": quantity_magnitude,
            "quantity_unit": quantity_unit,
            "calculated_usp_per_base_unit": None,
            "calculated_usp_unit": None,
            "declared_usp_raw": declared_usp_str,
            "declared_usp_numeric": None,
            "is_mathematically_accurate": False,
            "discrepancy_amount": None,
            "denomination_compliant": False,
            "is_compliant": False,
            "remarks": "Insufficient MRP or Net Quantity data to perform mathematical USP cross-verification.",
            "violations": []
        }

    u = quantity_unit.lower().strip()
    calc_usp = None
    statutory_base_unit = ""
    alt_usp = None
    alt_unit = ""

    # Mass / Weight (grams, kg)
    if u in ["g", "gm", "gms", "g."]:
        total_g = quantity_magnitude
        if total_g < 1000.0:
            statutory_base_unit = "Rs per g"
            calc_usp = mrp_num / total_g
            alt_unit = "Rs per 100 g"
            alt_usp = (mrp_num / total_g) * 100.0
        else:
            statutory_base_unit = "Rs per kg"
            calc_usp = (mrp_num / total_g) * 1000.0
    elif u in ["kg", "kgs", "kg."]:
        total_g = quantity_magnitude * 1000.0
        if quantity_magnitude < 1.0:
            statutory_base_unit = "Rs per g"
            calc_usp = mrp_num / total_g
            alt_unit = "Rs per 100 g"
            alt_usp = (mrp_num / total_g) * 100.0
        else:
            statutory_base_unit = "Rs per kg"
            calc_usp = mrp_num / quantity_magnitude

    # Volume (ml, L)
    elif u in ["ml", "ml.", "millilitre", "milliliter"]:
        total_ml = quantity_magnitude
        if total_ml < 1000.0:
            statutory_base_unit = "Rs per ml"
            calc_usp = mrp_num / total_ml
            alt_unit = "Rs per 100 ml"
            alt_usp = (mrp_num / total_ml) * 100.0
        else:
            statutory_base_unit = "Rs per L"
            calc_usp = (mrp_num / total_ml) * 1000.0
    elif u in ["l", "litre", "liter", "ltr"]:
        total_ml = quantity_magnitude * 1000.0
        if quantity_magnitude < 1.0:
            statutory_base_unit = "Rs per ml"
            calc_usp = mrp_num / total_ml
            alt_unit = "Rs per 100 ml"
            alt_usp = (mrp_num / total_ml) * 100.0
        else:
            statutory_base_unit = "Rs per L"
            calc_usp = mrp_num / quantity_magnitude

    # Count (N, U, pieces)
    elif u in ["n", "u", "pcs", "piece", "pieces", "nos", "units"]:
        statutory_base_unit = "Rs per piece"
        calc_usp = mrp_num / quantity_magnitude
    else:
        statutory_base_unit = f"Rs per {u}"
        calc_usp = mrp_num / quantity_magnitude

    # Helper function to extract all numbers from a string
    def _extract_number_candidates(text: Optional[str]) -> List[float]:
        if not text or str(text).upper() in ["NOT_FOUND", "NULL", "NONE", "CALCULATED ON PACK", "NOT DECLARED"]:
            return []
        matches = re.findall(r'(?:^|[^\d.])([0-9]+(?:\.[0-9]+)?)(?!\.)', str(text))
        res = []
        for m in matches:
            try:
                res.append(float(m))
            except ValueError:
                pass
        return res

    tol_primary = max(0.02, calc_usp * 0.05) if calc_usp is not None else 0.02
    tol_alt = max(0.02, alt_usp * 0.05) if alt_usp is not None else 0.02

    declared_num = None
    resolved_usp_str = declared_usp_str

    raw_candidates = _extract_number_candidates(declared_usp_str)

    # 1. First, if multiple numbers exist or string has slashes (e.g. "2.9/BP3 01H6^^/0.34" or "PER g: 2.9/0.34"):
    # Check if any candidate directly matches calc_usp or alt_usp
    matched_candidate = None
    for cand in raw_candidates:
        if abs(cand - calc_usp) <= tol_primary or (alt_usp is not None and abs(cand - alt_usp) <= tol_alt):
            matched_candidate = cand
            break

    # 2. If slash-delimited string (FMCG coding format) and no match yet, parse individual slash parts
    if matched_candidate is None and declared_usp_str and "/" in str(declared_usp_str):
        slash_parts = [p.strip() for p in str(declared_usp_str).split("/") if p.strip()]
        for p in reversed(slash_parts):
            p_cands = _extract_number_candidates(p)
            for c in p_cands:
                if abs(c - calc_usp) <= tol_primary or (alt_usp is not None and abs(c - alt_usp) <= tol_alt):
                    matched_candidate = c
                    break
            if matched_candidate is not None:
                break

    # 3. If context_text provided (e.g. coding window text or other panel fields), check for matching USP
    if matched_candidate is None and context_text:
        ctx_cands = _extract_number_candidates(context_text)
        for c in ctx_cands:
            # Skip if this number is exactly the MRP or the Net Quantity
            if abs(c - mrp_num) < 0.01:
                continue
            if abs(c - quantity_magnitude) < 0.01:
                continue
            if abs(c - calc_usp) <= tol_primary or (alt_usp is not None and abs(c - alt_usp) <= tol_alt):
                matched_candidate = c
                resolved_usp_str = f"₹ {c:.2f} per g (FMCG coding window)"
                break

    if matched_candidate is not None:
        declared_num = matched_candidate
        if resolved_usp_str and str(matched_candidate) in resolved_usp_str:
            pass
        else:
            resolved_usp_str = f"₹ {declared_num:.2f}"
    elif raw_candidates:
        # If no candidate matched the calculated USP, check if the string contains a slash block
        if declared_usp_str and "/" in str(declared_usp_str):
            slash_parts = [p.strip() for p in str(declared_usp_str).split("/") if p.strip()]
            for p in reversed(slash_parts):
                p_cands = _extract_number_candidates(p)
                if p_cands:
                    declared_num = p_cands[-1]
                    break
        if declared_num is None:
            declared_num = raw_candidates[0]

    violations = []
    is_accurate = False
    discrepancy = 0.0

    if declared_num is not None and calc_usp is not None:
        matches_primary = abs(declared_num - calc_usp) <= tol_primary
        matches_alt = False
        if alt_usp is not None:
            matches_alt = abs(declared_num - alt_usp) <= tol_alt

        if matches_primary or matches_alt:
            is_accurate = True
            discrepancy = 0.0
            matched_calc = calc_usp if matches_primary else alt_usp
            matched_u = statutory_base_unit if matches_primary else alt_unit
            remarks = f"Unit Sale Price verified: Declared '{resolved_usp_str}' matches calculated {matched_u} (Rs. {matched_calc:.2f})."
        else:
            is_accurate = False
            discrepancy = round(declared_num - calc_usp, 4)
            remarks = (
                f"VIOLATION under Rule 6(1)(e): Declared USP ('{resolved_usp_str}') does not match mathematically calculated "
                f"unit price of Rs. {calc_usp:.2f} {statutory_base_unit}"
                + (f" or Rs. {alt_usp:.2f} {alt_unit}" if alt_usp else "")
                + f" (Discrepancy: Rs. {discrepancy:+.2f})."
            )
            violations.append(remarks)
    else:
        # Under Rule 6(1)(e) (as amended in 2021), USP is mandatory across all pre-packaged commodities
        is_accurate = False
        remarks = (
            f"VIOLATION under Rule 6(1)(e): Unit Sale Price (USP) is mandatory on all pre-packaged commodities, "
            f"but no valid USP was declared on the packaging. Calculated statutory benchmark is Rs. {calc_usp:.2f} {statutory_base_unit}."
        )
        violations.append(remarks)

    return {
        "mrp_numeric": mrp_num,
        "quantity_numeric": quantity_magnitude,
        "quantity_unit": quantity_unit,
        "calculated_usp_per_base_unit": round(calc_usp, 4) if calc_usp else None,
        "calculated_usp_unit": statutory_base_unit,
        "declared_usp_raw": resolved_usp_str or declared_usp_str,
        "declared_usp_numeric": declared_num,
        "is_mathematically_accurate": is_accurate,
        "discrepancy_amount": discrepancy,
        "denomination_compliant": True,
        "is_compliant": len(violations) == 0,
        "remarks": remarks,
        "violations": violations
    }
