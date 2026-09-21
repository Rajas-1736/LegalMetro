import os
import sys
import uuid
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.scan_job import ScanJob
from app.models.rule_config import RuleConfig
import json
from app.core.security import get_password_hash
from app.config import settings

def create_synthetic_label_image(filename: str, product_name: str, declarations: list, is_compliant: bool = True):
    """Creates realistic product label image with clean text blocks."""
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    filepath = os.path.join(settings.STORAGE_LOCAL_DIR, filename)
    if os.path.exists(filepath):
        return

    width, height = 800, 600
    bg_color = (248, 250, 252) if is_compliant else (254, 242, 242)
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Load TrueType font if available
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_hdr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        font_val = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception:
        font_title = font_hdr = font_label = font_val = None

    # Outer border
    draw.rectangle([10, 10, width - 10, height - 10], outline=(30, 58, 138), width=3)
    draw.rectangle([20, 20, width - 20, 80], fill=(30, 58, 138))
    
    # Title
    draw.text((35, 35), product_name.upper(), fill=(255, 255, 255), font=font_title)
    draw.text((width - 270, 42), "MANDATORY DECLARATION PANEL", fill=(203, 213, 225), font=font_hdr)

    # Declarations
    y = 110
    for title, text in declarations:
        draw.text((40, y), f"{title}:", fill=(15, 23, 42), font=font_label)
        draw.text((280, y), text, fill=(51, 65, 85), font=font_val)
        draw.line([(35, y + 38), (width - 35, y + 38)], fill=(226, 232, 240), width=1)
        y += 55

    img.save(filepath, "JPEG")

def run_seed():
    print("=== Initializing LegalMetro AI Seed Data ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Demo Users
        users_data = [
            {
                "email": "admin@visionx.gov.in",
                "password": "admin123",
                "full_name": "Dr. Rajesh Sharma",
                "role": UserRole.ADMIN.value,
                "designation": "Director of Legal Metrology Enforcement",
                "badge_number": "VX-DIR-001"
            },
            {
                "email": "inspector@visionx.gov.in",
                "password": "inspector123",
                "full_name": "Sejal Sharma",
                "role": UserRole.INSPECTOR.value,
                "designation": "Senior Metrology Enforcement Officer",
                "badge_number": "VX-MH-4018"
            },
            {
                "email": "viewer@visionx.gov.in",
                "password": "viewer123",
                "full_name": "Arjun Patel",
                "role": UserRole.VIEWER.value,
                "designation": "Consumer Rights & Industry Observer",
                "badge_number": "VX-OBS-1002"
            },
            {
                "email": "admin@legalmetro.gov.in",
                "password": "admin123",
                "full_name": "Dr. Rajesh Sharma",
                "role": UserRole.ADMIN.value,
                "designation": "Director of Legal Metrology Enforcement",
                "badge_number": "LM-DIR-001"
            },
            {
                "email": "inspector@legalmetro.gov.in",
                "password": "inspector123",
                "full_name": "Sejal Sharma",
                "role": UserRole.INSPECTOR.value,
                "designation": "Senior Metrology Enforcement Officer",
                "badge_number": "LM-MH-4018"
            },
            {
                "email": "viewer@legalmetro.gov.in",
                "password": "viewer123",
                "full_name": "Arjun Patel",
                "role": UserRole.VIEWER.value,
                "designation": "Consumer Rights & Industry Observer",
                "badge_number": "LM-OBS-1002"
            }
        ]

        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    designation=u["designation"],
                    badge_number=u["badge_number"],
                    is_active=True
                )
                db.add(user)
        db.commit()
        print("-> Users seeded successfully.")

        inspector = db.query(User).filter(User.email == "inspector@legalmetro.gov.in").first()

        # 2. Seed Rule Configs
        rules_json_path = os.path.join(os.path.dirname(__file__), "..", "app", "rules", "legal_metrology_2011.json")
        try:
            with open(rules_json_path, "r", encoding="utf-8") as f:
                default_rules = json.load(f)
        except Exception:
            default_rules = []
        for r in default_rules:
            existing_rule = db.query(RuleConfig).filter(RuleConfig.rule_id == r["rule_id"]).first()
            if not existing_rule:
                rc = RuleConfig(
                    rule_id=r["rule_id"],
                    clause_reference=r["clause_reference"],
                    title=r["title"],
                    description=r["description"],
                    field_key=r["field_key"],
                    severity=r.get("severity", "MANDATORY_VIOLATION"),
                    is_active=r.get("is_active", True),
                    parameters=r.get("parameters", {})
                )
                db.add(rc)
        db.commit()
        print("-> Legal Metrology Rules seeded.")

        # 3. Seed Realistic Sample Products and Inspection History
        products_seed = [
            {
                "name": "Britannia NutriChoice Digestive Biscuits",
                "brand": "Britannia",
                "category": "Packaged Food",
                "mfr": "Britannia Industries Ltd, 5/1A Hungerford Street, Kolkata - 700017",
                "net_qty": "250 g",
                "mrp": "MRP ₹ 45.00 (inclusive of all taxes)",
                "mfg": "Mfg Date: 02/2026",
                "care": "1800-425-4449, feedback@britannia.co.in",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 1
            },
            {
                "name": "Puro Refined Sunflower Cooking Oil 1L",
                "brand": "Puro",
                "category": "Beverages & Oils",
                "mfr": "Puro Agro Foods Pvt Ltd, Plot 42, MIDC Industrial Area, Pune 411018",
                "net_qty": "1 L",
                "mrp": "MRP Rs 165.00", # Missing 'inclusive of all taxes'
                "mfg": "Packed: 01/2026",
                "care": "Toll Free 1800-200-1122, care@purofoods.in",
                "coo": "India",
                "status": "NON_COMPLIANT",
                "score": 75.0,
                "days_ago": 2
            },
            {
                "name": "Belgian Delights Dark Chocolate 150g",
                "brand": "Belgian Delights",
                "category": "Imported Goods",
                "mfr": "Imported & Marketed by Euro Gourmet Ltd, Andheri East, Mumbai 400069",
                "net_qty": "150 g",
                "mrp": "MRP ₹ 350.00 (incl. of all taxes)",
                "mfg": "Import Date: 12/2025",
                "care": "customercare@eurogourmet.in",
                "coo": None, # Missing Country of Origin on imported product
                "status": "NON_COMPLIANT",
                "score": 75.0,
                "days_ago": 2
            },
            {
                "name": "Himalaya Purifying Neem Face Wash",
                "brand": "Himalaya",
                "category": "Cosmetics & Toiletries",
                "mfr": "The Himalaya Drug Company, Makali, Bangalore - 562162",
                "net_qty": "150 ml",
                "mrp": "MRP ₹ 180.00 (inclusive of all taxes)",
                "mfg": "Batch MFG: 02/2026",
                "care": None, # Missing consumer care
                "coo": "India",
                "status": "NON_COMPLIANT",
                "score": 75.0,
                "days_ago": 3
            },
            {
                "name": "UltraClean Active Detergent Powder",
                "brand": "UltraClean",
                "category": "Household Chemicals",
                "mfr": "UltraClean Consumer Care Ltd, GIDC Estate, Vadodara 390010",
                "net_qty": "500 gms", # Illegal unit 'gms'
                "mrp": "MRP ₹ 60.00 (inclusive of all taxes)",
                "mfg": "Mfg: 01/2026",
                "care": "0265-224455, help@ultraclean.com",
                "coo": "India",
                "status": "NON_COMPLIANT",
                "score": 62.5,
                "days_ago": 3
            },
            {
                "name": "Tata Sampann Organic Turmeric Powder",
                "brand": "Tata Sampann",
                "category": "Packaged Food",
                "mfr": "Tata Consumer Products Ltd, 1 Bishop Lefroy Road, Kolkata 700020",
                "net_qty": "100 g",
                "mrp": "MRP ₹ 38.00 (inclusive of all taxes)",
                "mfg": "Packed: 02/2026",
                "care": "1800-108-4488, care@tataconsumer.com",
                "coo": "India",
                "status": "FLAGGED_FOR_REVIEW",
                "score": 87.5,
                "days_ago": 4
            },
            {
                "name": "Bisleri Packaged Natural Spring Water 1L",
                "brand": "Bisleri",
                "category": "Beverages & Oils",
                "mfr": "Bisleri International Pvt Ltd, Western Express Highway, Mumbai 400099",
                "net_qty": "1 L",
                "mrp": "MRP ₹ 20.00 (inclusive of all taxes)",
                "mfg": "Mfg Date: 03/2026",
                "care": "1800-121-1007, wecare@bisleri.co.in",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 5
            },
            {
                "name": "Dettol Original Germ Protection Soap",
                "brand": "Dettol",
                "category": "Cosmetics & Toiletries",
                "mfr": "Reckitt Benckiser India Pvt Ltd, DLF Cyber City, Gurugram 122002",
                "net_qty": "125 g",
                "mrp": "MRP ₹ 55.00 (inclusive of all taxes)",
                "mfg": "Mfg: 01/2026",
                "care": "1800-102-6012, consumer.relations@reckitt.com",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 5
            },
            {
                "name": "Amul Pure Ghee Pouch 500ml",
                "brand": "Amul",
                "category": "Packaged Food",
                "mfr": "Gujarat Cooperative Milk Marketing Federation Ltd, Anand 388001",
                "net_qty": "500 ml",
                "mrp": "MRP ₹ 315.00 (inclusive of all taxes)",
                "mfg": "Pkd: 02/2026",
                "care": "1800-258-3333, customercare@amul.coop",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 6
            },
            {
                "name": "Syska Smart LED Bulb 9W",
                "brand": "Syska",
                "category": "Consumer Electronics",
                "mfr": "SSK Electrotech Pvt Ltd, Pune Nagar Road, Pune 411014",
                "net_qty": "1 N",
                "mrp": "MRP ₹ 399.00 (inclusive of all taxes)",
                "mfg": "Month/Year: 02/2026",
                "care": "1800-102-8787, support@syska.co.in",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 6
            },
            {
                "name": "Cadbury Dairy Milk Silk Chocolate",
                "brand": "Cadbury",
                "category": "Packaged Food",
                "mfr": "Mondelez India Foods Pvt Ltd, Indiqube Infinity, Bengaluru 560068",
                "net_qty": "150 g",
                "mrp": "MRP ₹ 175.00 (inclusive of all taxes)",
                "mfg": "Mfg: 02/2026",
                "care": "1800-22-7080, suggestions@mdlz.com",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 7
            },
            {
                "name": "Surf Excel Easy Wash Detergent 1kg",
                "brand": "Surf Excel",
                "category": "Household Chemicals",
                "mfr": "Hindustan Unilever Limited, B.D. Sawant Marg, Chakala, Andheri Mumbai 400099",
                "net_qty": "1 kg",
                "mrp": "MRP ₹ 140.00 (inclusive of all taxes)",
                "mfg": "Mfg Date: 01/2026",
                "care": "1800-10-22-221, lever.care@unilever.com",
                "coo": "India",
                "status": "COMPLIANT",
                "score": 100.0,
                "days_ago": 7
            }
        ]

        for p_idx, p_data in enumerate(products_seed):
            existing_prod = db.query(Product).filter(Product.product_name == p_data["name"]).first()
            if not existing_prod:
                created_dt = datetime.utcnow() - timedelta(days=p_data["days_ago"], hours=p_idx)
                prod = Product(
                    product_name=p_data["name"],
                    brand_name=p_data["brand"],
                    category=p_data["category"],
                    manufacturer_name=p_data["mfr"],
                    declared_net_quantity=p_data["net_qty"],
                    declared_mrp=p_data["mrp"],
                    latest_compliance_status=p_data["status"],
                    inspection_count=1,
                    created_at=created_dt,
                    updated_at=created_dt
                )
                db.add(prod)
                db.flush()

                # Generate image
                image_filename = f"sample_{p_idx + 1}.jpg"
                decs = [
                    ("Generic Name", p_data["name"]),
                    ("Manufacturer", p_data["mfr"]),
                    ("Net Quantity", p_data["net_qty"]),
                    ("MRP", p_data["mrp"]),
                    ("Mfg/Packing Date", p_data["mfg"]),
                    ("Consumer Care", p_data["care"] or "NOT DECLARED"),
                    ("Country of Origin", p_data["coo"] or "NOT DECLARED"),
                ]
                create_synthetic_label_image(image_filename, p_data["name"], decs, is_compliant=(p_data["status"] == "COMPLIANT"))

                # Create structured extracted fields
                extracted_data = {
                    "generic_name": {"value": p_data["name"], "label": "Commodity Name", "status": "found", "confidence": 0.98, "bbox": {"x": 5.0, "y": 5.0, "width": 60.0, "height": 8.0}},
                    "manufacturer_details": {"value": p_data["mfr"], "label": "Manufacturer Details", "status": "found", "confidence": 0.95, "bbox": {"x": 5.0, "y": 20.0, "width": 80.0, "height": 10.0}},
                    "net_quantity": {"value": p_data["net_qty"], "label": "Net Quantity", "status": "found" if "gms" not in p_data["net_qty"] else "invalid", "confidence": 0.96, "bbox": {"x": 5.0, "y": 32.0, "width": 30.0, "height": 8.0}},
                    "mrp": {"value": p_data["mrp"], "label": "MRP Declaration", "status": "found" if "taxes" in p_data["mrp"] else "invalid", "confidence": 0.97, "bbox": {"x": 5.0, "y": 42.0, "width": 45.0, "height": 8.0}},
                    "mfg_date": {"value": p_data["mfg"], "label": "Mfg Date", "status": "found", "confidence": 0.93, "bbox": {"x": 5.0, "y": 52.0, "width": 35.0, "height": 8.0}},
                    "consumer_care": {"value": p_data["care"], "label": "Consumer Care", "status": "found" if p_data["care"] else "missing", "confidence": 0.94 if p_data["care"] else 0.0, "bbox": {"x": 5.0, "y": 62.0, "width": 55.0, "height": 8.0} if p_data["care"] else None},
                    "country_of_origin": {"value": p_data["coo"], "label": "Country of Origin", "status": "found" if p_data["coo"] else "missing", "confidence": 0.92 if p_data["coo"] else 0.0, "bbox": {"x": 5.0, "y": 72.0, "width": 30.0, "height": 8.0} if p_data["coo"] else None},
                    "is_imported": p_data["category"] == "Imported Goods"
                }

                # Evaluate rules
                is_comp = (p_data["status"] == "COMPLIANT")
                is_flagged = (p_data["status"] == "FLAGGED_FOR_REVIEW")
                rule_results = [
                    {
                        "rule_id": "RULE_6_1_A",
                        "clause_reference": "Rule 6(1)(a)",
                        "title": "Manufacturer Name & Complete Address",
                        "description": "Name and complete address of the manufacturer or packer",
                        "field_key": "manufacturer_details",
                        "status": "PASS",
                        "severity": "MANDATORY_VIOLATION",
                        "remarks": "Valid manufacturer name and physical address identified."
                    },
                    {
                        "rule_id": "RULE_6_1_B",
                        "clause_reference": "Rule 6(1)(b)",
                        "title": "Common or Generic Commodity Name",
                        "description": "Generic name of the commodity on the principal display panel",
                        "field_key": "generic_name",
                        "status": "PASS",
                        "severity": "MANDATORY_VIOLATION",
                        "remarks": "Generic commodity name declared clearly."
                    },
                    {
                        "rule_id": "RULE_6_1_C",
                        "clause_reference": "Rule 6(1)(c) read with Rule 13",
                        "title": "Net Quantity & Metric Measurement Standard",
                        "description": "Net quantity in standard international metric units",
                        "field_key": "net_quantity",
                        "status": "FAIL" if "gms" in p_data["net_qty"] else "PASS",
                        "severity": "MANDATORY_VIOLATION",
                        "remarks": "Illegal non-standard unit 'gms' used." if "gms" in p_data["net_qty"] else "Standard metric unit declared correctly."
                    },
                    {
                        "rule_id": "RULE_6_1_E",
                        "clause_reference": "Rule 6(1)(e)",
                        "title": "Maximum Retail Price (MRP)",
                        "description": "Retail sale price inclusive of all taxes",
                        "field_key": "mrp",
                        "status": "FAIL" if "taxes" not in p_data["mrp"].lower() else "PASS",
                        "severity": "MANDATORY_VIOLATION",
                        "remarks": "Missing mandatory phrase 'incl. of all taxes'." if "taxes" not in p_data["mrp"].lower() else "MRP declared with statutory tax declaration."
                    },
                    {
                        "rule_id": "RULE_6_1_F",
                        "clause_reference": "Rule 6(1)(f)",
                        "title": "Consumer Care Redressal Mechanism",
                        "description": "Telephone helpline number and email address",
                        "field_key": "consumer_care",
                        "status": "PASS" if p_data["care"] else "FAIL",
                        "severity": "MANDATORY_VIOLATION",
                        "remarks": "Verified active telephone and email contact." if p_data["care"] else "Consumer redressal helpline missing."
                    },
                    {
                        "rule_id": "RULE_7",
                        "clause_reference": "Rule 7 read with Second Schedule",
                        "title": "Minimum Numeral Height (Font Scale Audit)",
                        "description": "Statutory minimum character height in millimeters",
                        "field_key": "font_scale",
                        "status": "NEEDS_REVIEW" if is_flagged else "PASS",
                        "severity": "WARNING",
                        "remarks": "Reference scale not detected; manual mm verification required." if is_flagged else "Numeral height complies with Schedule II minimum thresholds."
                    }
                ]

                scan = ScanJob(
                    id=f"scan-seed-{p_idx + 1:03d}-{uuid.uuid4().hex[:6]}",
                    product_id=prod.id,
                    inspector_id=inspector.id if inspector else None,
                    image_url=f"/api/v1/storage/file/{image_filename}",
                    reference_scale_mm=85.0 if p_data["status"] != "FLAGGED_FOR_REVIEW" else None,
                    status="COMPLETED",
                    progress_percentage=100,
                    current_stage_message="Inspection verification completed.",
                    overall_compliance_verdict=p_data["status"],
                    compliance_score=p_data["score"],
                    extracted_data=extracted_data,
                    rule_results=rule_results,
                    raw_ocr_tokens=[
                        {"text": p_data["name"], "bbox": {"x": 5.0, "y": 5.0, "width": 60.0, "height": 8.0}, "confidence": 0.98, "engine": "paddleocr"},
                        {"text": p_data["mfr"], "bbox": {"x": 5.0, "y": 20.0, "width": 80.0, "height": 10.0}, "confidence": 0.95, "engine": "reconciled_agreement"},
                        {"text": p_data["net_qty"], "bbox": {"x": 5.0, "y": 32.0, "width": 30.0, "height": 8.0}, "confidence": 0.96, "engine": "paddleocr"},
                        {"text": p_data["mrp"], "bbox": {"x": 5.0, "y": 42.0, "width": 45.0, "height": 8.0}, "confidence": 0.97, "engine": "reconciled_agreement"},
                    ],
                    inspector_notes=f"Routine verification inspection conducted at retail distribution center. Status marked as {p_data['status']}.",
                    created_at=created_dt,
                    completed_at=created_dt + timedelta(minutes=1)
                )
                db.add(scan)

        db.commit()
        print("-> 12 Realistic Indian Packaged Commodities and inspections seeded.")
        print("=== Seed Completed Successfully ===")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
