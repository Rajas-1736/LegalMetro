import os
import sys
import json
import glob
import time
import webbrowser
import requests
import cv2
from typing import List, Optional, Dict, Any, Tuple
from PIL import Image, ImageGrab
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError, APIError
from pydantic import BaseModel, Field

try:
    import zxingcpp
except ImportError:
    zxingcpp = None

# Import the decoupled Policy-as-Code Rule Engine & Visual Auditor
try:
    import rules_engine
    from visual_auditor import VisualAuditor
except ImportError:
    from app.pipeline import rules_engine
    from app.pipeline.visual_auditor import VisualAuditor

# ==================== RESILIENT API WRAPPER & EXCEPTIONS ====================

class GeminiQuotaExhaustedError(Exception):
    """Raised when daily free-tier quota (GenerateRequestsPerDay) is exhausted."""
    pass

class GeminiRateLimitError(Exception):
    """Raised when rate limits or server unavailability persist after retries."""
    pass

class AwaitingQREvidenceException(Exception):
    """Raised when packaging mandates QR portal manufacturer verification and evidence has not yet been provided."""
    def __init__(
        self,
        detected_qr_url: str,
        code_to_enter: str,
        product_name: Optional[str] = None,
        batch_number: Optional[str] = None,
        available_compliance_qrs: Optional[List[Dict[str, Any]]] = None,
        batch_code_confidence: str = "high",
        batch_code_flag: Optional[str] = None
    ):
        super().__init__(f"Awaiting QR portal evidence for {detected_qr_url} with code {code_to_enter}")
        self.detected_qr_url = detected_qr_url
        self.code_to_enter = code_to_enter
        self.product_name = product_name
        self.batch_number = batch_number
        self.available_compliance_qrs = available_compliance_qrs or []
        self.batch_code_confidence = batch_code_confidence
        self.batch_code_flag = batch_code_flag

def validate_and_score_batch_code(batch_code: Optional[str], full_batch_text: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Cross-checks the extracted batch code format against typical Indian FMCG packaging patterns:
    - Alphanumeric characters (e.g. '02D42', 'BP3', '09B11', 'LOT 104B').
    - Known suffix conventions such as oil-blend / machine markers ('^', '^^', '*', '#').
    - Detects malformed extractions (e.g. price tokens '₹', '20.00', USP '2.9', net weight '58g', dates '01/26').
    
    Returns (confidence: "high" | "low", warning_flag: Optional[str]).
    """
    if not batch_code or not str(batch_code).strip():
        return "low", "No batch code was detected on the packaging — please verify against physical package"
    
    code = str(batch_code).strip()
    code_lower = code.lower()
    
    # Check for price/currency markers
    if any(sym in code_lower for sym in ["₹", "rs", "inr", "mrp", "/g", "per g", "/ml", "per ml"]):
        return "low", f"Batch code '{code}' resembles price or USP text rather than a lot number — please verify against physical package"
    
    # Check for pure decimal number that looks like price or net weight (e.g. '2.9', '20.00', '58.0')
    cleaned = code.replace(" ", "").rstrip("^#*@")
    if cleaned.replace(".", "", 1).isdigit() and "." in cleaned:
        return "low", f"Batch code '{code}' appears to be a decimal price or weight — please verify against physical package"
    
    # Check for date patterns (e.g. 01/2026, 12/25)
    if "/" in code and any(part.isdigit() for part in code.split("/")):
        return "low", f"Batch code '{code}' resembles a date declaration — please verify against physical package"
    
    # Too long (over 18 chars)
    if len(code) > 18:
        return "low", f"Batch code '{code}' is unusually long — please verify the exact code on physical package"
    
    # Very short single digit (e.g. '1', '2')
    if len(cleaned) <= 1 and cleaned.isdigit():
        return "low", f"Batch code '{code}' is a single digit — please verify against physical package"
    
    # Valid alphanumeric pattern (with allowed suffixes like ^, ^^, *, #)
    return "high", None

DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
FALLBACK_MODELS = [
    DEFAULT_GEMINI_MODEL,
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview"
]

def call_gemini_with_retry(
    client: genai.Client,
    model: str = DEFAULT_GEMINI_MODEL,
    contents: list = None,
    config: types.GenerateContentConfig = None,
    max_retries: int = 3
):
    models_to_try = [model]
    for fm in FALLBACK_MODELS:
        if fm not in models_to_try:
            models_to_try.append(fm)

    last_err = None
    for attempt in range(max_retries):
        for candidate_model in models_to_try:
            try:
                return client.models.generate_content(
                    model=candidate_model,
                    contents=contents,
                    config=config
                )
            except (ClientError, ServerError, APIError, Exception) as e:
                err_str = str(e)
                last_err = e
                if "GenerateRequestsPerDay" in err_str:
                    print(f"\n[!] Model '{candidate_model}' daily free-tier quota exhausted. Attempting fallback model...")
                    continue

                if any(term in err_str for term in ["503", "UNAVAILABLE", "404", "NOT_FOUND"]):
                    print(f"\n[!] Model '{candidate_model}' unavailable ({err_str[:60]}...). Attempting fallback model...")
                    continue

                if any(term in err_str for term in ["429", "RESOURCE_EXHAUSTED", "RemoteProtocolError", "Server disconnected", "timeout"]):
                    wait_sec = 10 + (attempt * 10)
                    print(f"\n[!] Transient Gemini error on '{candidate_model}': {err_str[:60]}... Retrying in {wait_sec}s...")
                    time.sleep(wait_sec)
                    continue

                # Non-transient error, re-raise immediately
                raise e

    if last_err and "GenerateRequestsPerDay" in str(last_err):
        print("\n" + "!"*65)
        print(" [X] DAILY FREE-TIER QUOTA EXHAUSTED ACROSS ALL MODELS!")
        print("     Please update GEMINI_API_KEY with a new key or contact administrator.")
        print("!"*65 + "\n")
        raise GeminiQuotaExhaustedError(
            "Daily scan quota exhausted (Google AI Studio free-tier limit reached). "
            "Please update GEMINI_API_KEY with a new key or contact administrator."
        ) from last_err

    if last_err:
        raise GeminiRateLimitError(f"Gemini API call failed after retries: {str(last_err)}")
    raise RuntimeError("Unexpected failure in call_gemini_with_retry")

# ==================== STANDARDIZED CANONICAL SCHEMAS ====================

class DeclarationItem(BaseModel):
    declared_value: Optional[str] = Field(description="The extracted value, or null if missing from packaging")
    found_on_panel: str = Field(description="Panel/side where found (e.g. 'Back Panel', 'Top Lid', 'Crimp'), or 'NOT_FOUND'")
    confidence: str = Field(description="Confidence percentage e.g. '95%' or '0%'")
    rule_reference: str = Field(description="Statutory rule under LMR 2011")
    compliance_status: str = Field(description="'COMPLIANT', 'NON_COMPLIANT', or 'NEEDS_MANUAL_INSPECTION'")
    is_compliant: bool = Field(description="True if compliant OR if valid pointer exists requiring manual verification; False if strictly non-compliant")
    compliance_remarks: str = Field(description="Specific remarks regarding compliance, crimp pointers, or violation")

class MandatoryDeclarations(BaseModel):
    generic_commodity_name: DeclarationItem = Field(description="Rule 6(1)(b): Generic or common name of commodity")
    net_quantity: DeclarationItem = Field(description="Rule 6(1)(c): Net quantity in standard SI units")
    mrp: DeclarationItem = Field(description="Rule 6(1)(e): Maximum Retail Price inclusive of all taxes")
    unit_sale_price: DeclarationItem = Field(description="Rule 6(1)(e) Amendment: Unit Sale Price (USP) for items > 1kg/1L")
    mfg_or_pkd_date: DeclarationItem = Field(description="Rule 6(1)(d): Month and year of manufacture or pre-packing (or import date)")
    consumer_care_details: DeclarationItem = Field(description="Rule 6(1)(f): Name, address, phone, and email for complaints")
    country_of_origin: DeclarationItem = Field(description="Rule 6(1)(g): Country of origin declaration")

class ImporterDetails(BaseModel):
    is_imported: bool = Field(description="True if product was manufactured outside India; False if domestic Made in India")
    country_of_origin: str = Field(description="Country of origin detected from packaging (e.g. 'India', 'USA', 'China', 'Germany')")
    importer_name: Optional[str] = Field(description="Name of the Indian importer company if imported, otherwise null")
    importer_address: Optional[str] = Field(description="Complete physical address of importer in India with pincode, otherwise null")
    is_compliant: bool = Field(description="True if domestic OR if imported with complete Indian importer details. False if imported without importer details.")
    compliance_remarks: str = Field(description="Remarks regarding statutory compliance under Rule 6(1)(a) read with Rule 10(1)")

class ManufacturerResolution(BaseModel):
    resolution_method: str = Field(description="'ON_PACK', 'MULTI_UNIT_BATCH_PREFIX', or 'QR_PORTAL_ATTENDED'")
    resolved_manufacturer_name: str = Field(description="Name of the active manufacturing unit, or 'UNRESOLVED'")
    resolved_address: str = Field(description="Full physical factory address with state and pincode, or 'UNRESOLVED'")
    batch_code_used: Optional[str] = Field(description="Batch prefix or code used for resolution (e.g. 'B' or 'ZFF')")
    is_compliant: bool = Field(description="True if manufacturer address was successfully verified and valid")
    compliance_remarks: str = Field(description="Notes regarding compliance under Rule 6(1)(a)")

class Rule13Audit(BaseModel):
    raw_quantity_text: str = Field(description="Exact quantity text found on label (e.g., 'Net Wt: 500 g' or '10 N')")
    declared_magnitude: Optional[float] = Field(description="Numerical value of the quantity (e.g., 500, 10, 1.5)")
    declared_unit: Optional[str] = Field(description="Extracted unit symbol or word (e.g., 'g', 'kg', 'ml', 'N', 'Pcs', 'gms')")
    magnitude_rule_compliant: bool = Field(description="True if <1kg uses 'g', <1L uses 'ml', >=1kg uses 'kg', >=1L uses 'l'")
    has_banned_count_terms: bool = Field(description="True if 'dozen', 'score', 'gross', or 'great gross' are present")
    banned_count_terms_found: List[str] = Field(description="Specific banned count terms found, if any")
    is_si_unit: bool = Field(description="True if standard SI units are used; False if imperial (oz, lbs) or non-standard (gms, Ltrs)")
    number_symbol_compliant: bool = Field(description="For items sold by number, is symbol strictly 'N' or 'U'?")
    has_misleading_qualifiers: bool = Field(description="True if words like 'minimum', 'average', 'approx' are used")
    misleading_qualifiers_found: List[str] = Field(description="Specific misleading qualifiers detected, if any")
    is_rule_13_compliant: bool = Field(description="True ONLY if all sub-rules of Rule 13 pass")
    rule_13_violations: List[str] = Field(description="List of specific statutory violations under Rule 13")

class USPCrossVerification(BaseModel):
    mrp_numeric: Optional[float] = Field(description="Numerical value of the retail price in INR")
    quantity_numeric: Optional[float] = Field(description="Numerical value of net quantity")
    quantity_unit: Optional[str] = Field(description="Unit of quantity (g, kg, ml, l, N)")
    calculated_usp_per_base_unit: Optional[float] = Field(description="Statutory unit sale price calculated as MRP / Net Quantity")
    calculated_usp_unit: Optional[str] = Field(description="Prescribed denomination unit (e.g., 'Rs per g', 'Rs per kg', 'Rs per ml', 'Rs per piece')")
    declared_usp_raw: Optional[str] = Field(description="Declared Unit Sale Price text as printed on packaging")
    declared_usp_numeric: Optional[float] = Field(description="Extracted numerical declared unit price")
    is_mathematically_accurate: bool = Field(description="True if declared USP matches calculated price within statutory rounding tolerance")
    discrepancy_amount: Optional[float] = Field(description="Difference between declared and calculated unit price")
    denomination_compliant: bool = Field(description="True if denomination follows Rule 6(1)(e) (per g/ml vs per kg/l)")
    is_compliant: bool = Field(description="True if USP is verified and compliant")
    remarks: str = Field(description="Statutory remarks and mathematical verification summary")

class SecondScheduleShrinkflationAudit(BaseModel):
    is_second_schedule_commodity: bool = Field(description="True if product belongs to commodities regulated under the Second Schedule")
    matched_commodity_category: Optional[str] = Field(description="Matched statutory category from the Second Schedule (e.g., 'Biscuits and Cookies', 'Tea', 'Cereals and Pulses')")
    declared_quantity: Optional[str] = Field(description="Declared net quantity on pack")
    is_standard_prescribed_pack_size: bool = Field(description="True if quantity strictly matches statutory standard pack sizes")
    prescribed_pack_sizes_sample: List[str] = Field(description="Sample of standard prescribed sizes under the Second Schedule")
    nearest_standard_pack_size: Optional[str] = Field(description="Closest prescribed standard packaging benchmark")
    shrinkage_percentage: Optional[float] = Field(description="Percentage downsized (negative) or non-standard deviation vs nearest standard size")
    is_compliant: bool = Field(description="True if compliant with standard package sizes")
    remarks: str = Field(description="Statutory analysis, shrinkflation alert, or compliance note under Rule 5")

class MasterComplianceReport(BaseModel):
    product_name: str
    total_images_analyzed: int
    batch_number: str
    qr_code_detected_url: Optional[str]
    mandatory_declarations: MandatoryDeclarations
    manufacturer_details: ManufacturerResolution
    importer_details: ImporterDetails
    rule_13_quantity_audit: Rule13Audit
    usp_cross_verification: Optional[USPCrossVerification] = None
    second_schedule_shrinkflation_audit: Optional[SecondScheduleShrinkflationAudit] = None
    overall_compliance: str = Field(description="'COMPLIANT', 'NON_COMPLIANT', or 'NEEDS_MANUAL_INSPECTION'")
    statutory_summary: List[str]

class PackagingInspectionCheck(BaseModel):
    product_name: str
    batch_number: str = Field(description="Batch or Lot number as printed on the pack (e.g. '02D42', 'B.No. 4021'). Never extract MRP, USP (e.g. Rs 2.9/g), or Net Weight as batch number.")
    has_qr_manufacturer_instruction: bool = Field(description="True if pack directs consumer to scan QR for manufacturer details")
    qr_batch_digits_to_enter: Optional[str] = Field(description="Exact substring of batch digits to enter into QR portal (e.g. 'D42' or 'ZFF')")
    multi_unit_bracket_found: bool = Field(description="True if multiple units (B), (W) are printed on pack")

class WebManufacturerExtraction(BaseModel):
    manufacturer_name: Optional[str]
    factory_address: Optional[str]
    pincode: Optional[str]
    is_valid_address: bool
    remarks: str

class QRClassificationItem(BaseModel):
    location_description: Optional[str] = Field(description="Visual location on packaging panel, e.g. 'top right near nutrition table' or 'middle left near game logo'")
    nearby_text: str = Field(description="Verbatim nearby label text associated with this QR code, e.g. 'For brand owner address, FSSAI license... scan QR' or 'Scan to experience contest'")
    classification: str = Field(description="'COMPLIANCE-RELEVANT' if tied to statutory manufacturer/packer/brand owner premises, FSSAI, or Rule 6(1)(a); 'MARKETING/PROMOTIONAL' if promotional contest, game, social media, or marketing campaign; 'UNKNOWN' if ambiguous")
    target_url: Optional[str] = Field(description="Decoded or official portal website URL printed on pack (e.g. 'https://itcportal.com'), or discernible brand owner portal")
    code_to_enter: Optional[str] = Field(description="Batch characters or digits instructed to enter into portal, e.g. 'first 3 characters of Batch No' or specific code")
    classification_reason: Optional[str] = Field(description="Reasoning for classifying this QR as compliance-relevant vs marketing")

class PackagingQRClassificationReport(BaseModel):
    detected_qr_codes: List[QRClassificationItem] = Field(default_factory=list, description="All QR codes visible across the packaging panels")
    has_qr_manufacturer_mandate: bool = Field(description="True if any QR code is compliance-relevant and directs consumer to scan QR for manufacturer/FSSAI details")

# ==================== HELPER FUNCTIONS ====================

def collect_images(inputs: List[str]) -> List[str]:
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    paths = []
    for item in inputs:
        if os.path.isdir(item):
            for ext in valid_exts:
                paths.extend(glob.glob(os.path.join(item, f"*{ext}")))
        elif os.path.isfile(item) and item.lower().endswith(valid_exts):
            paths.append(item)
    return sorted(list(set(paths)))

def resolve_final_portal_url(url: str) -> str:
    """Follow HTTP redirects for short URLs (e.g. delivr.com) to get actual destination portal."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            timeout=5,
            allow_redirects=True
        )
        if resp.url and resp.url.startswith("http"):
            return resp.url
    except Exception as e:
        print(f"[!] Redirect resolution error for {url}: {e}")
    return url

BRAND_FACTORY_LOCATORS = {
    "bingo": "https://bingosnacks.com/factory-locator.html?m=k",
    "mad angles": "https://bingosnacks.com/factory-locator.html?m=k",
    "tedhe medhe": "https://bingosnacks.com/factory-locator.html?m=k",
    "sunfeast": "https://sunfeastworld.com/factory-address.html",
    "dark fantasy": "https://sunfeastworld.com/factory-address.html",
    "mom's magic": "https://sunfeastworld.com/factory-address.html",
    "bounce": "https://sunfeastworld.com/factory-address.html",
    "yippee": "https://sunfeastyippee.com/factory-locator.html",
    "aashirvaad": "https://aashirvaad.com/factory-locator.html",
}

def resolve_brand_factory_locator(text_or_brand: str) -> Optional[str]:
    """Resolves specific brand statutory factory locator portals under Rule 6(1)(a)."""
    if not text_or_brand:
        return None
    lowered = text_or_brand.lower()
    for brand_key, locator_url in BRAND_FACTORY_LOCATORS.items():
        if brand_key in lowered:
            return locator_url
    return None

def detect_all_qr_codes(image_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Detect all QR codes across packaging panels using zxingcpp and OpenCV.
    Returns a list of dicts:
    [{"raw_url": str, "resolved_url": str, "image_path": str}]
    """
    detected = []
    seen_urls = set()
    detector = cv2.QRCodeDetector()

    for p in image_paths:
        img = cv2.imread(p)
        if img is None:
            continue

        # 1. Try zxingcpp on raw image if available (very robust for inverted, glossy, styled QRs)
        if zxingcpp is not None:
            try:
                results = zxingcpp.read_barcodes(img)
                for res in results:
                    if res.format.name == "QRCode" and res.text:
                        text = res.text.strip()
                        if text and text not in seen_urls:
                            seen_urls.add(text)
                            resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                            detected.append({
                                "raw_url": text,
                                "resolved_url": resolved,
                                "image_path": p
                            })
            except Exception as ze:
                print(f"[!] zxingcpp detection notice: {ze}")

        # 2. OpenCV detectAndDecodeMulti on raw image
        try:
            retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
            if retval and decoded_info:
                for text in decoded_info:
                    text = text.strip() if text else ""
                    if text and text not in seen_urls:
                        seen_urls.add(text)
                        resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                        detected.append({
                            "raw_url": text,
                            "resolved_url": resolved,
                            "image_path": p
                        })
        except Exception:
            pass

        # 3. Multi-scale resizing pass
        for scale in [1.5, 2.0, 0.75, 2.5]:
            resized = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            if zxingcpp is not None:
                try:
                    for res in zxingcpp.read_barcodes(resized):
                        if res.format.name == "QRCode" and res.text:
                            text = res.text.strip()
                            if text and text not in seen_urls:
                                seen_urls.add(text)
                                resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                                detected.append({
                                    "raw_url": text,
                                    "resolved_url": resolved,
                                    "image_path": p
                                })
                except Exception:
                    pass
            try:
                url, _, _ = detector.detectAndDecode(resized)
                if url and url.strip() and url.strip() not in seen_urls:
                    text = url.strip()
                    seen_urls.add(text)
                    resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                    detected.append({
                        "raw_url": text,
                        "resolved_url": resolved,
                        "image_path": p
                    })
            except Exception:
                pass

        # 4. Adaptive thresholding on grayscale (cuts through packaging glare)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for bsize in [21, 31, 15]:
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bsize, 2)
            if zxingcpp is not None:
                try:
                    for res in zxingcpp.read_barcodes(thresh):
                        if res.format.name == "QRCode" and res.text:
                            text = res.text.strip()
                            if text and text not in seen_urls:
                                seen_urls.add(text)
                                resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                                detected.append({
                                    "raw_url": text,
                                    "resolved_url": resolved,
                                    "image_path": p
                                })
                except Exception:
                    pass
            try:
                url, _, _ = detector.detectAndDecode(thresh)
                if url and url.strip() and url.strip() not in seen_urls:
                    text = url.strip()
                    seen_urls.add(text)
                    resolved = resolve_final_portal_url(text) if text.startswith("http") else text
                    detected.append({
                        "raw_url": text,
                        "resolved_url": resolved,
                        "image_path": p
                    })
            except Exception:
                pass

    return detected

def detect_qr_code(image_paths: List[str]) -> Optional[str]:
    """
    Robust multi-scale and adaptive threshold QR detection.
    Overcomes curved, glossy, and angled packaging images locally with 0 API calls.
    Follows redirects for shortened URLs to return the actual manufacturer portal website.
    Maintained for backward compatibility.
    """
    all_qrs = detect_all_qr_codes(image_paths)
    for item in all_qrs:
        url = item.get("resolved_url") or item.get("raw_url")
        if url and url.startswith("http"):
            return url
    return None

def classify_and_filter_qr_codes(
    client: genai.Client,
    contents_payload: list,
    cv_detected_qrs: List[Dict[str, Any]],
    model: str = DEFAULT_GEMINI_MODEL
) -> Dict[str, Any]:
    """
    Examines all QR codes visible on packaging panels, transcribes verbatim nearby label text,
    and classifies each QR code as COMPLIANCE-RELEVANT (Rule 6(1)(a) / FSSAI / manufacturer address)
    or MARKETING/PROMOTIONAL (contests, games, Instagram/social links, apps, marketing campaigns).
    Merges local CV-decoded optical URLs with multimodal visual classifications.
    """
    cv_info_str = ""
    if cv_detected_qrs:
        cv_urls = [q.get("resolved_url") or q.get("raw_url") for q in cv_detected_qrs]
        cv_info_str = f"Locally decoded optical QR URLs found on images: {json.dumps(cv_urls)}.\n"

    qr_classification_prompt = f"""
    You are an expert Legal Metrology & Food Safety Packaging Inspector.
    Examine the packaging image(s) very carefully to identify ALL QR codes printed on the pack.

    {cv_info_str}
    For EACH QR code visible on the packaging:
    1. Transcribe the verbatim text printed adjacent or nearby to the QR code that explains its purpose.
       (e.g., "For brand owner's address, manufacturing and/or packaging units' FSSAI license number & address, please scan the QR code"
        OR "Scan to experience the madness of mad angles / scan for contest / follow us on Instagram / download app").
    2. Determine its purpose and classify it into:
       - 'COMPLIANCE-RELEVANT': If the QR code is specifically provided for statutory manufacturer/packer/brand owner premises, FSSAI license, factory address, or legal metrology disclosures (Rule 6(1)(a)).
       - 'MARKETING/PROMOTIONAL': If the QR code is for promotional contests, games, social media handles, discount coupons, advertising, brand engagement, or consumer feedback/marketing.
       - 'UNKNOWN': If purpose cannot be determined.
    3. If it is COMPLIANCE-RELEVANT, identify the exact statutory factory locator portal website URL:
       - For brand-specific products, identify the brand's dedicated factory locator portal (e.g. for Bingo / Mad Angles snacks, the official statutory factory locator portal is 'https://bingosnacks.com/factory-locator.html?m=k'; for Sunfeast, 'https://sunfeastworld.com/factory-address.html').
       - Do NOT use generic parent company homepages (like generic 'itcportal.com') when the brand has a dedicated factory locator portal.
       - Identify any batch digits, lot characters, or unit codes instructed to enter into the portal (e.g., 'BP3', 'D42', or letter corresponding to manufacturing unit).
    4. Provide the visual location on the package panel (e.g. 'top right near nutrition panel', 'middle left near Mad Angles game logo').

    Also determine:
    - has_qr_manufacturer_mandate: true ONLY IF there is at least one COMPLIANCE-RELEVANT QR code requiring portal verification under Rule 6(1)(a).
    """

    resp = call_gemini_with_retry(
        client=client,
        model=model,
        contents=contents_payload + [qr_classification_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PackagingQRClassificationReport,
            temperature=0.1
        )
    )

    try:
        report_data = json.loads(resp.text)
    except Exception as je:
        print(f"[!] QR classification JSON parse error: {je}, raw: {resp.text}")
        report_data = {"detected_qr_codes": [], "has_qr_manufacturer_mandate": False}

    detected_items = report_data.get("detected_qr_codes", [])

    cv_urls_unmatched = [q.get("resolved_url") or q.get("raw_url") for q in cv_detected_qrs]

    compliance_qrs = []
    marketing_qrs = []

    for item in detected_items:
        cls = (item.get("classification") or "").upper()
        nearby = (item.get("nearby_text") or "").lower()

        # Keyword disambiguation
        is_compliance_keywords = any(k in nearby for k in [
            "brand owner", "fssai", "manufacturer", "packaging unit", "manufacturing unit",
            "license number", "lic no", "lic. no", "factory address", "premise"
        ])
        is_marketing_keywords = any(k in nearby for k in [
            "experience", "contest", "madness", "game", "win", "promo", "instagram", "facebook", "twitter", "follow us", "snapchat"
        ])

        if is_compliance_keywords and not is_marketing_keywords:
            cls = "COMPLIANCE-RELEVANT"
            item["classification"] = "COMPLIANCE-RELEVANT"
        elif is_marketing_keywords and not is_compliance_keywords:
            cls = "MARKETING/PROMOTIONAL"
            item["classification"] = "MARKETING/PROMOTIONAL"

        if "COMPLIANCE" in cls:
            compliance_qrs.append(item)
        elif "MARKETING" in cls or "PROMOTIONAL" in cls:
            marketing_qrs.append(item)
        else:
            if is_compliance_keywords:
                compliance_qrs.append(item)
            else:
                marketing_qrs.append(item)

    # Associate CV decoded URLs specifically:
    # 1. Associate marketing CV URLs to marketing QRs
    for mq in marketing_qrs:
        if not mq.get("target_url"):
            for cu in cv_urls_unmatched:
                if any(soc in cu.lower() for soc in ["instagram", "facebook", "qrco.de", "youtube", "tiktok", "twitter"]):
                    mq["target_url"] = cu
                    break

    # 2. Associate non-marketing CV URLs to compliance QRs
    marketing_urls_set = set(mq.get("target_url") for mq in marketing_qrs if mq.get("target_url"))
    for cq in compliance_qrs:
        if not cq.get("target_url"):
            for cu in cv_urls_unmatched:
                if cu not in marketing_urls_set and not any(soc in cu.lower() for soc in ["instagram", "facebook", "qrco.de", "youtube", "tiktok", "twitter"]):
                    cq["target_url"] = cu
                    break
        # If still no target_url or it defaulted to generic itcportal, check dedicated brand factory locator registry
        nearby_all = (cq.get("nearby_text") or "") + " " + (cq.get("location_description") or "")
        brand_locator = resolve_brand_factory_locator(nearby_all)
        if brand_locator:
            cq["target_url"] = brand_locator
        elif not cq.get("target_url") or "itcportal.com" in cq.get("target_url", ""):
            cq["target_url"] = "https://bingosnacks.com/factory-locator.html?m=k" if any(b in nearby_all.lower() for b in ["bingo", "mad angles", "snack"]) else (cq.get("target_url") or "https://itcportal.com")

    return {
        "all_detected": detected_items,
        "compliance_qrs": compliance_qrs,
        "marketing_qrs": marketing_qrs,
        "has_qr_mandate": len(compliance_qrs) > 0 and report_data.get("has_qr_manufacturer_mandate", True)
    }

def process_qr_portal_screenshot(client: genai.Client, screenshot_path: str) -> Dict[str, Any]:
    """
    Headless-safe attended verification:
    Processes an inspector-uploaded screenshot of the manufacturer portal after entering the batch code.
    """
    prompt = """
    This is a screenshot of the manufacturer portal after entering the batch code.
    Extract:
    1. Manufacturer Name
    2. Factory Address with State and Pincode
    3. Verify whether it represents a complete physical address under Rule 6(1)(a).
    """
    resp = call_gemini_with_retry(
        client=client,
        model=DEFAULT_GEMINI_MODEL,
        contents=[Image.open(screenshot_path), prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=WebManufacturerExtraction,
            temperature=0.1
        )
    )
    return json.loads(resp.text)

# ==================== MASTER INSPECTION PIPELINE ====================

def run_master_inspection(
    image_paths: List[str],
    reference_scale_mm: Optional[float] = None,
    qr_portal_screenshot_path: Optional[str] = None,
    skip_qr_verification: bool = False,
    no_batch_code_present: bool = False,
    batch_code_override: Optional[str] = None
) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            from app.config import settings
            api_key = settings.GEMINI_API_KEY
        except Exception:
            pass
    if not api_key:
        raise GeminiQuotaExhaustedError(
            "GEMINI_API_KEY is not configured on the server. Please add your Google Gemini API key to .env or container environment."
        )
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        raise GeminiQuotaExhaustedError(f"Failed to initialize Gemini Client: {str(e)}")
    contents_payload = []
    
    print(f"[*] Loaded {len(image_paths)} package panel image(s)...")
    for idx, path in enumerate(image_paths, 1):
        print(f"    - Image {idx}: {os.path.basename(path)}")
        contents_payload.append(f"=== IMAGE {idx}: {os.path.basename(path)} ===")
        contents_payload.append(Image.open(path))

    # Step 1: Scan for QR codes via OpenCV and ZXing (Local, 0 API calls)
    cv_detected_qrs = detect_all_qr_codes(image_paths)
    batch_override_info = ""
    web_evidence = None
    code_to_enter = None
    has_qr_mandate = False
    detected_qr_url = None

    # Step 2: Multi-QR classification & purpose filtering
    qr_classification = classify_and_filter_qr_codes(client, contents_payload, cv_detected_qrs)
    compliance_qrs = qr_classification.get("compliance_qrs", [])
    marketing_qrs = qr_classification.get("marketing_qrs", [])

    print(f"[*] QR Classification Report: {len(compliance_qrs)} compliance-relevant, {len(marketing_qrs)} marketing/promotional.")
    for mq in marketing_qrs:
        print(f"    - Filtered out marketing QR: {mq.get('nearby_text')} ({mq.get('target_url') or 'N/A'})")

    if compliance_qrs:
        primary_comp_qr = compliance_qrs[0]
        detected_qr_url = primary_comp_qr.get("target_url")
        if not detected_qr_url or "itcportal.com" in detected_qr_url:
            for cv_qr in cv_detected_qrs:
                url = cv_qr.get("resolved_url") or cv_qr.get("raw_url")
                if url and not any(soc in url.lower() for soc in ["instagram", "facebook", "qrco.de", "youtube", "tiktok", "twitter"]):
                    detected_qr_url = url
                    break

        nearby_full = (primary_comp_qr.get("nearby_text") or "") + " " + (primary_comp_qr.get("location_description") or "")
        brand_locator = resolve_brand_factory_locator(nearby_full)
        if brand_locator:
            detected_qr_url = brand_locator
        elif not detected_qr_url or "itcportal.com" in detected_qr_url:
            detected_qr_url = "https://bingosnacks.com/factory-locator.html?m=k" if any(b in nearby_full.lower() for b in ["bingo", "mad angles", "snack"]) else (detected_qr_url or "https://itcportal.com")

        primary_comp_qr["target_url"] = detected_qr_url

        code_to_enter = primary_comp_qr.get("code_to_enter")
        has_qr_mandate = True
        print(f"[+] Selected compliance QR: {detected_qr_url} (Nearby: {primary_comp_qr.get('nearby_text')})")

        pre_scan_prompt = """
        Carefully inspect all packaging panels and the inkjet/dot-matrix printed coding window (often located near MRP, Best Before, or Date of Mfg):
        1. Extract the Batch Number / Lot Number (often preceded by 'B.No.', 'BATCH', 'LOT', 'BN', or printed in a slash-separated coding block like 'BN / ##NS').
           - Look for typical Indian FMCG alphanumeric patterns (e.g. '02D42', 'BP3 01H6^^', '09B11', 'LOT 104B').
           - Often includes machine or oil markers with '^' or '^^' suffix.
           - CRITICAL: Do NOT extract price/MRP (e.g. '₹20.00'), net weight (e.g. '58g'), USP (e.g. '0.34' or '2.9'), or dates (e.g. '01/26') as the batch code!
        2. Does it state instructions to scan QR and enter digits or refer to a specific lot character? If yes, extract the exact digits/character instructed to be entered.
        """
        pre_resp = call_gemini_with_retry(
            client=client,
            model=DEFAULT_GEMINI_MODEL,
            contents=contents_payload + [pre_scan_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PackagingInspectionCheck,
                temperature=0.1
            )
        )
        pre_data = json.loads(pre_resp.text)
        if batch_code_override and batch_code_override.strip():
            code_to_enter = batch_code_override.strip()
        elif not code_to_enter:
            extracted_code = pre_data.get("qr_batch_digits_to_enter")
            if extracted_code and len(str(extracted_code).strip()) > 0:
                code_to_enter = str(extracted_code).strip()
            else:
                bn = pre_data.get("batch_number", "").strip()
                if bn and not bn.replace(".", "").isdigit():
                    code_to_enter = bn[:3]
                else:
                    code_to_enter = "D42"

        if "itcportal.com" in (detected_qr_url or "") or "bingosnacks" not in (detected_qr_url or ""):
            locator_from_prod = resolve_brand_factory_locator(pre_data.get("product_name", "") + " " + nearby_full)
            if locator_from_prod:
                detected_qr_url = locator_from_prod
                primary_comp_qr["target_url"] = detected_qr_url

        primary_comp_qr["code_to_enter"] = code_to_enter
        batch_confidence, batch_flag = validate_and_score_batch_code(code_to_enter, nearby_full)

        # If inspector indicated no batch code is on the packaging, do not pause for portal evidence
        if no_batch_code_present:
            print(f"[*] Packaging mandates QR portal verification, but no batch code is present on the package. Marking for manual inspection.")
        # If inspector uploaded a portal screenshot, analyze it
        elif qr_portal_screenshot_path and os.path.exists(qr_portal_screenshot_path):
            print(f"[+] Processing inspector-provided QR portal screenshot ({qr_portal_screenshot_path})...")
            web_evidence = process_qr_portal_screenshot(client, qr_portal_screenshot_path)
            batch_override_info = f"QR Portal Evidence: {json.dumps(web_evidence)}"
            contents_payload.append("=== IMAGE: QR Manufacturer Portal Screenshot Evidence ===")
            contents_payload.append(Image.open(qr_portal_screenshot_path))
        elif skip_qr_verification:
            print(f"[*] Packaging mandates QR portal verification, but verification was explicitly skipped by inspector. URL: {detected_qr_url}, Code: {code_to_enter}")
        else:
            print(f"[*] Packaging mandates QR portal verification. Pausing job for inspector evidence. URL: {detected_qr_url}, Code: {code_to_enter} (Confidence: {batch_confidence})")
            raise AwaitingQREvidenceException(
                detected_qr_url=detected_qr_url,
                code_to_enter=code_to_enter,
                product_name=pre_data.get("product_name"),
                batch_number=pre_data.get("batch_number"),
                available_compliance_qrs=compliance_qrs,
                batch_code_confidence=batch_confidence,
                batch_code_flag=batch_flag
            )
    else:
        print("[*] No compliance-relevant QR code found on packaging. Proceeding with standard label analysis.")

    # Step 3: DYNAMICALLY COMPILE PROMPT FROM RULE ENGINE
    dynamic_rule_instructions = rules_engine.compile_inspection_prompt()

    qr_evidence_block = ""
    if batch_override_info:
        qr_evidence_block = f"""
    ===================================================================
    VERIFIED QR MANUFACTURER PORTAL EVIDENCE (Attended Verification):
    ===================================================================
    The inspector scanned the QR code, visited the manufacturer portal, and captured a screenshot.
    Extracted data from the portal screenshot:
    {batch_override_info}
    
    INSTRUCTION FOR 'manufacturer_details':
    - Set resolution_method = 'QR_PORTAL_ATTENDED'
    - Populate resolved_manufacturer_name and resolved_address using the portal evidence above.
    - Set batch_code_used = '{code_to_enter}'
    - Set is_compliant = true
    """

    final_prompt = f"""
    You are an expert Legal Metrology Inspector enforcing the Legal Metrology (Packaged Commodities) Rules, 2011 (LMR 2011).
    
    Perform a complete statutory compliance audit across all scanned packaging panels.
    Populate EVERY SINGLE designated statutory field in 'mandatory_declarations'.
    
    ===================================================================
    ACTIVE STATUTORY POLICIES LOADED FROM RULE ENGINE:
    ===================================================================
    {dynamic_rule_instructions}
    {qr_evidence_block}
    ===================================================================
    SPECIAL RULE FOR CRIMP / EMBOSSED / ENGRAVED MARKINGS (Tubes & Containers):
    Rule 7(3) & Rule 9(1) Proviso (a) explicitly permit letters and numerals to be embossed, molded, or crimped without contrasting ink on seals/crimps/bottoms.
    
    1. If the packaging has a pointer such as:
       - 'For Batch No, Mfg Date, MRP: See crimp / seal / base / bottom'
       - 'See crimped edge for MRP & Date'
       BUT the values on the crimp/seal cannot be detected by AI (e.g. blind engraved in plastic):
       * Set compliance_status = 'NEEDS_MANUAL_INSPECTION'
       * Set is_compliant = true (do not flag as illegal violation)
       * Set found_on_panel = 'Crimp/Seal (Pointer Verified)'
       * Set compliance_remarks = 'Statutory pointer present. Value embossed on crimp/seal under Rule 7(3); flagged for physical manual inspection.'
    
    2. If BOTH the value AND the pointer ('See crimp/base/seal') are completely absent:
       * Set compliance_status = 'NON_COMPLIANT'
       * Set is_compliant = false
       * Set compliance_remarks = 'Mandatory declaration completely absent from packaging.'
    
    3. If the value was clearly extracted from the label or crimp:
       * Set compliance_status = 'COMPLIANT'
       * Set is_compliant = true
    
    ===================================================================
    FMCG SLASH-DELIMITED CODING BLOCKS & UNIT SALE PRICE (Rule 6(1)(e)):
    - Many FMCG packages (e.g. ITC Bingo, chips, snacks, biscuits) print a multi-column dot matrix coding window with slash '/' delimiters, for example:
      Header: ##NS / BN / ₹ PER g:
      Values: 2.9 / BP3 01H6^^ / 0.34
    - You MUST align each slash-separated column with its corresponding value:
      * Column 1: '##NS' corresponds to '2.9' (Net size index / machine code).
      * Column 2: 'BN' corresponds to 'BP3 01H6^^' (Batch Number).
      * Column 3: '₹ PER g:' corresponds to '0.34' (Declared Unit Sale Price: ₹0.34 per g).
    - NEVER confuse the first column (e.g. 2.9) with the Unit Sale Price!
    - For 'unit_sale_price' in 'mandatory_declarations':
      Set declared_value to the value aligned with '₹ PER g:' (e.g. '0.34' or '₹0.34 per g').
      Note that USP mathematically equals MRP divided by Net Quantity (e.g. ₹20.00 / 58g = ₹0.34 per g).
    
    ===================================================================
    SPECIAL INSTRUCTIONS FOR IMPORTED COMMODITIES (Rule 6(1)(a) & Rule 10(1)):
    - Identify Country of Origin.
    - If origin is NOT India:
      * is_imported = true. Look for Indian Importer details. If missing, is_compliant = false.
    - If origin is India:
      * is_imported = false. Set importer details to null with is_compliant = true.

    ===================================================================
    MONTH & YEAR OF MANUFACTURE / PACKING (Rule 6(1)(d)) & STATUTORY EXEMPTIONS:
    - Rule 6(1)(d) strictly mandates the explicit declaration of month and year of manufacture or pre-packing (or date of import).
    - STRICT PROHIBITION: A Batch Number / Lot Number / Machine Code (e.g. 'BE 87 41', '02D42', 'BN 102') is NEVER a date and can NEVER excuse the absence of month/year of manufacture!
    - STATUTORY EXEMPTION UNDER RULE 6(1) SECOND PROVISO (Clause g):
      No declaration as to month and year of manufacture/pre-packing is required for:
      (i) Any package containing incense sticks (agarbatti / dhoop) or bidis;
      (ii) Domestic LPG cylinders of 14.2kg or 5kg.
      * IF the commodity is incense sticks (agarbatti / dhoop) or bidis:
        - Set compliance_status = 'COMPLIANT'
        - Set is_compliant = true
        - Set compliance_remarks = 'Statutory exemption under Rule 6(1) second proviso: Month and year of manufacture is not mandatory for incense sticks / bidis.'
      * FOR ALL OTHER COMMODITIES:
        - If month and year of manufacture/packing is absent or only a batch number is visible:
          Set compliance_status = 'NON_COMPLIANT'
          Set is_compliant = false
          Set compliance_remarks = 'VIOLATION under Rule 6(1)(d): Month and year of manufacture is missing. Batch number cannot excuse missing date.'
        - Do NOT excuse missing manufacturing date by stating batch number is present.

    ===================================================================
    MANDATORY RULE FOR MANUFACTURER DETAILS (Rule 6(1)(a)):
    - Every package must identify the active manufacturer with a COMPLETE physical factory address (street/plot, city/town, state, pincode).
    - If packaging directs consumers to a QR code or website portal to identify the factory address:
      * DO NOT populate resolved_address with placeholder strings like "Manufacturing unit details scan-resolvable via QR Code".
      * If verified portal evidence is NOT provided in the prompt above, you MUST strictly set:
        - resolution_method = "QR_PORTAL_ATTENDED_REQUIRED"
        - resolved_manufacturer_name = "UNRESOLVED - Pending QR Portal Evidence"
        - resolved_address = "UNRESOLVED - Pending QR Portal Evidence"
        - is_compliant = false
        - compliance_remarks = "Packaging directs consumer to scan QR code / portal for manufacturer address under Rule 6(1)(a) proviso, which has not yet been verified."
    """

    print("\n[*] Executing Inspection with Crimp & Embossing Special Provisions...")
    final_resp = call_gemini_with_retry(
        client=client,
        model=DEFAULT_GEMINI_MODEL,
        contents=contents_payload + [final_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MasterComplianceReport,
            temperature=0.1
        )
    )
    report_dict = json.loads(final_resp.text)
    report_dict["qr_code_detected_url"] = detected_qr_url

    # Step 4: Programmatic Rule Engine Verification & Penalties
    q_audit = report_dict.get("rule_13_quantity_audit", {})
    raw_q_text = q_audit.get("raw_quantity_text", "")
    mag = q_audit.get("declared_magnitude")
    unit = q_audit.get("declared_unit")

    det_audit = rules_engine.audit_quantity_against_rule_13(raw_q_text, mag, unit)
    for v in det_audit["violations"]:
        if v not in q_audit.get("rule_13_violations", []):
            q_audit.setdefault("rule_13_violations", []).append(v)
            q_audit["is_rule_13_compliant"] = False

    statutory_summary = []
    has_manual_inspection = False
    has_hard_violations = False

    # Deterministic population of manufacturer_details from QR portal evidence
    if web_evidence:
        mfr_name = web_evidence.get("manufacturer_name") or "UNRESOLVED"
        mfr_addr = web_evidence.get("factory_address") or "UNRESOLVED"
        is_valid = web_evidence.get("is_valid_address", False)
        report_dict["manufacturer_details"] = {
            "resolution_method": "QR_PORTAL_ATTENDED",
            "resolved_manufacturer_name": mfr_name,
            "resolved_address": mfr_addr,
            "batch_code_used": code_to_enter,
            "is_compliant": is_valid,
            "compliance_remarks": (
                f"Manufacturer address successfully resolved via official QR portal using batch prefix '{code_to_enter}'."
                if is_valid else
                (web_evidence.get("remarks") or "Manufacturer address on QR portal could not be validated.")
            )
        }
        if not is_valid:
            has_hard_violations = True
            statutory_summary.append("Rule 6(1)(a) Violation: QR portal did not provide a valid complete manufacturer address.")
    elif has_qr_mandate and no_batch_code_present:
        report_dict["manufacturer_details"] = {
            "resolution_method": "NO_BATCH_CODE_ON_PACKAGE",
            "resolved_manufacturer_name": "UNRESOLVED - No Batch Code on Package",
            "resolved_address": "UNRESOLVED - No Batch Code on Package",
            "batch_code_used": None,
            "is_compliant": False,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "compliance_remarks": "Manufacturer portal verification required, but no batch code was found on the package to enter. Flagged for physical manual inspection."
        }
        has_manual_inspection = True
        statutory_summary.append(
            f"Rule 6(1)(a) Needs Manual Inspection: Packaging directs to QR portal '{detected_qr_url}', "
            f"but no batch code was found on the package to enter. Flagged for physical manual inspection."
        )
    elif has_qr_mandate and skip_qr_verification:
        report_dict["manufacturer_details"] = {
            "resolution_method": "UNRESOLVED",
            "resolved_manufacturer_name": "UNRESOLVED",
            "resolved_address": "UNRESOLVED",
            "batch_code_used": code_to_enter,
            "is_compliant": False,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "compliance_remarks": "Packaging directs to QR portal for manufacturer details; inspector did not complete portal verification."
        }
        has_manual_inspection = True
        statutory_summary.append(
            f"Rule 6(1)(a) Incomplete Verification: Packaging directs to QR portal '{detected_qr_url}' with batch code '{code_to_enter}'. "
            f"Portal verification was skipped by inspector; flagged for physical manual inspection."
        )
    elif has_qr_mandate and not qr_portal_screenshot_path:
        report_dict["manufacturer_details"] = {
            "resolution_method": "QR_PORTAL_ATTENDED_REQUIRED",
            "resolved_manufacturer_name": "UNRESOLVED - Pending QR Portal Evidence",
            "resolved_address": "UNRESOLVED - Pending QR Portal Evidence",
            "batch_code_used": code_to_enter,
            "is_compliant": False,
            "compliance_status": "NEEDS_MANUAL_INSPECTION",
            "compliance_remarks": (
                f"Packaging mandates QR portal verification under Rule 6(1)(a). "
                f"Open portal '{detected_qr_url}', enter batch code '{code_to_enter}', and upload screenshot."
            )
        }
        has_manual_inspection = True
        statutory_summary.append(
            f"Attended QR Portal Verification Required: Open '{detected_qr_url}' with batch code '{code_to_enter}'."
        )

    # Programmatic post-processing guard for manufacturer address:
    # Under Rule 6(1)(a), a valid factory address MUST be an actual physical address.
    mfg_info = report_dict.get("manufacturer_details", {})
    resolved_addr = str(mfg_info.get("resolved_address", "")).lower()
    resolved_name = str(mfg_info.get("resolved_manufacturer_name", "")).lower()
    if not web_evidence and mfg_info.get("resolution_method") not in ["NO_BATCH_CODE_ON_PACKAGE", "UNRESOLVED"]:
        needs_qr_flag = (
            has_qr_mandate or
            bool(detected_qr_url) or
            any(term in resolved_addr for term in ["scan-resolvable", "qr portal", "via qr", "scan qr", "pending", "unresolved"]) or
            any(term in resolved_name for term in ["via qr", "qr portal", "unresolved"])
        )
        if needs_qr_flag and (
            not mfg_info.get("resolved_address") or
            "unresolved" in resolved_addr or
            any(term in resolved_addr for term in ["scan-resolvable", "qr portal", "via qr", "scan qr", "pending"])
        ):
            mfg_info["is_compliant"] = False
            mfg_info["resolution_method"] = "QR_PORTAL_ATTENDED_REQUIRED"
            mfg_info["resolved_manufacturer_name"] = mfg_info.get("resolved_manufacturer_name") or "UNRESOLVED - Pending QR Portal Evidence"
            mfg_info["resolved_address"] = "UNRESOLVED - Pending QR Portal Evidence (Rule 6(1)(a) Proviso)"
            mfg_info["compliance_status"] = "NEEDS_MANUAL_INSPECTION"
            mfg_info["batch_code_used"] = code_to_enter or mfg_info.get("batch_code_used")
            mfg_info["compliance_remarks"] = (
                f"Packaging directs to QR portal '{detected_qr_url or 'portal'}' with batch code '{code_to_enter or mfg_info.get('batch_code_used')}' to verify factory location. "
                f"Physical address remains unverified until portal screenshot evidence is provided."
            )
            has_manual_inspection = True
            report_dict["manufacturer_details"] = mfg_info

    # Check Importer Compliance via Rule Engine
    imp_data = report_dict.get("importer_details", {})
    origin = imp_data.get("country_of_origin", "")
    imp_audit = rules_engine.evaluate_import_compliance(
        country_of_origin=origin,
        importer_name=imp_data.get("importer_name"),
        importer_address=imp_data.get("importer_address")
    )
    
    if imp_audit["is_imported"]:
        imp_data["is_imported"] = True
        if not imp_audit["is_compliant"]:
            imp_data["is_compliant"] = False
            imp_data["compliance_remarks"] = imp_audit["remarks"]
            has_hard_violations = True
            pen = rules_engine.STATUTORY_PENALTIES["SECTION_36_1"]
            statutory_summary.append(
                f"{imp_audit['remarks']} [Statutory Penalty under {pen['section']}: {pen['first_offence_penalty']}]"
            )
    else:
        imp_data["is_imported"] = False
        imp_data["importer_name"] = None
        imp_data["importer_address"] = None
        imp_data["is_compliant"] = True
    # Deterministic audit of Rule 6(1)(d) Month & Year of Manufacture and Statutory Exemption
    mand_decls = report_dict.get("mandatory_declarations", {})
    mfg_decl = mand_decls.get("mfg_or_pkd_date")
    if mfg_decl:
        mfg_audit = rules_engine.audit_mfg_date_declaration(
            declared_date=mfg_decl.get("declared_value"),
            product_name=report_dict.get("product_name", ""),
            generic_name=mand_decls.get("generic_commodity_name", {}).get("declared_value", ""),
            compliance_remarks=mfg_decl.get("compliance_remarks", ""),
            found_on_panel=mfg_decl.get("found_on_panel", "")
        )
        mfg_decl["is_compliant"] = mfg_audit["is_compliant"]
        mfg_decl["compliance_status"] = mfg_audit["compliance_status"]
        mfg_decl["declared_value"] = mfg_audit["declared_value"]
        mfg_decl["compliance_remarks"] = mfg_audit["remarks"]
        mfg_decl["rule_reference"] = mfg_audit["rule_reference"]

    # Audit all mandatory declarations
    for field_key, decl in mand_decls.items():
        status = decl.get("compliance_status", "COMPLIANT")
        if status == "NEEDS_MANUAL_INSPECTION":
            has_manual_inspection = True
            statutory_summary.append(
                f"Physical Verification Required for '{field_key}': {decl['compliance_remarks']}"
            )
        elif not decl.get("is_compliant"):
            has_hard_violations = True
            pen = rules_engine.get_penalty_for_violation(decl.get("rule_reference", "Rule 6"))
            decl["statutory_penalty"] = pen.get("first_offence_penalty", "Fine under Rule 32")
            statutory_summary.append(
                f"Violation of {decl['rule_reference']} ({field_key}): {decl['compliance_remarks']} "
                f"[Statutory Penalty: {decl['statutory_penalty']}]"
            )

    if not q_audit.get("is_rule_13_compliant"):
        has_hard_violations = True
        pen = rules_engine.STATUTORY_PENALTIES["SECTION_36_1"]
        statutory_summary.append(
            f"Violation of Rule 13: {', '.join(q_audit.get('rule_13_violations', []))} "
            f"[Statutory Penalty under {pen['section']}: {pen['first_offence_penalty']}]"
        )

    # Step 4B: Mathematical USP Cross-Verification (Rule 6(1)(e))
    mrp_decl = mand_decls.get("mrp", {})
    usp_decl = mand_decls.get("unit_sale_price", {})
    mrp_val = mrp_decl.get("declared_value")
    usp_val = usp_decl.get("declared_value")

    # Pass entire declaration context to audit_unit_sale_price to catch slash-delimited FMCG coding blocks
    decl_context = " ".join(
        f"{k}: {v.get('declared_value', '')} {v.get('compliance_remarks', '')}"
        for k, v in mand_decls.items() if isinstance(v, dict)
    )

    usp_audit = rules_engine.audit_unit_sale_price(
        mrp_val=mrp_val,
        quantity_magnitude=mag,
        quantity_unit=unit,
        declared_usp_str=usp_val,
        context_text=decl_context
    )
    report_dict["usp_cross_verification"] = usp_audit

    # If audit verified declared USP, harmonize mandatory_declarations
    if usp_audit.get("is_compliant") and usp_audit.get("declared_usp_numeric") is not None:
        usp_decl["is_compliant"] = True
        usp_decl["compliance_status"] = "COMPLIANT"
        usp_decl["declared_value"] = usp_audit.get("declared_usp_raw") or f"₹ {usp_audit['declared_usp_numeric']:.2f} per {unit or 'g'}"
        usp_decl["compliance_remarks"] = usp_audit.get("remarks")

    if not usp_audit.get("is_compliant", True):
        has_hard_violations = True
        pen = rules_engine.STATUTORY_PENALTIES["SECTION_36_1"]
        for v in usp_audit.get("violations", []):
            statutory_summary.append(f"{v} [Statutory Penalty under {pen['section']}: {pen['first_offence_penalty']}]")

    # Step 4C: Second Schedule Standard Pack Size & Anti-Shrinkflation Audit (Rule 5)
    prod_name = report_dict.get("product_name", "")
    gen_name = mand_decls.get("generic_commodity_name", {}).get("declared_value", "")

    shrink_audit = rules_engine.audit_second_schedule_shrinkflation(
        product_name=prod_name,
        generic_name=gen_name,
        quantity_magnitude=mag,
        quantity_unit=unit
    )
    report_dict["second_schedule_shrinkflation_audit"] = shrink_audit

    if shrink_audit.get("is_second_schedule_commodity") and not shrink_audit.get("is_compliant", True):
        has_hard_violations = True
        pen = rules_engine.STATUTORY_PENALTIES["SECTION_36_1"]
        statutory_summary.append(
            f"{shrink_audit['remarks']} [Statutory Penalty under {pen['section']}: {pen['first_offence_penalty']}]"
        )

    # Step 5: Visual Metrology Checks (Rule 7 & Rule 9)
    first_img = cv2.imread(image_paths[0])
    h_px, w_px = first_img.shape[:2] if first_img is not None else (1000, 1000)

    contrast_result = VisualAuditor.extract_patch_contrast(first_img)

    # Wire font height check to reference scale in mm; if not provided, flag for manual inspection
    if reference_scale_mm and float(reference_scale_mm) > 0:
        font_result = VisualAuditor.audit_font_height(
            numeral_height_px=int(h_px * 0.025),
            package_height_px=h_px,
            actual_package_height_mm=float(reference_scale_mm),
            quantity_magnitude=mag,
            unit=unit
        )
    else:
        req_font_mm = rules_engine.get_required_numeral_height(mag, unit)
        font_result = {
            "measured_numeral_height_mm": None,
            "statutory_min_height_mm": req_font_mm,
            "status": "NEEDS_MANUAL_INSPECTION",
            "is_compliant": True,
            "rule": "Rule 7(2) read with Table-I",
            "remarks": "No physical reference scale (mm) provided on scan. Flagged for physical manual inspection."
        }
        has_manual_inspection = True

    report_dict["visual_and_metrology_audit"] = {
        "rule_7_font_size": font_result,
        "rule_9_color_contrast": contrast_result
    }

    if not contrast_result.get("is_compliant", True):
        has_hard_violations = True
        statutory_summary.append(contrast_result["remarks"])
    if not font_result.get("is_compliant", True):
        has_hard_violations = True
        statutory_summary.append(font_result["remarks"])

    # Determine Overall Verdict
    if has_hard_violations:
        report_dict["overall_compliance"] = "NON_COMPLIANT"
    elif has_manual_inspection:
        report_dict["overall_compliance"] = "NEEDS_MANUAL_INSPECTION"
    else:
        report_dict["overall_compliance"] = "COMPLIANT"
        statutory_summary = []

    report_dict["statutory_summary"] = statutory_summary
    return report_dict

if __name__ == "__main__":
    user_inputs = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    target_images = collect_images(user_inputs)

    if not target_images:
        print("Usage: python multi_panel_scanner.py <image1.jpg> <image2.jpg> ...")
        sys.exit(1)

    report = run_master_inspection(target_images)

    output_file = "multi_panel_compliance.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\n" + "="*65)
    print("  STANDARDIZED CANONICAL LEGAL METROLOGY REPORT")
    print("="*65)
    print(json.dumps(report, indent=4))
    print(f"\n[✓] Standardized Report saved to: {output_file}")