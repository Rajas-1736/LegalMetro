import io
import pytest
from docx import Document
from app.pipeline.rules_engine import audit_unit_sale_price
from app.reports.pdf_generator import pdf_report_generator
from app.reports.docx_generator import docx_report_generator

def test_usp_fmcg_slash_coding():
    # 1. Full dot-matrix header and values
    r1 = audit_unit_sale_price(
        mrp_val='20.00',
        quantity_magnitude=58.0,
        quantity_unit='g',
        declared_usp_str='##NS/BN/ ₹ PER g: 2.9/BP3 01H6^^/0.34'
    )
    assert r1['declared_usp_numeric'] == 0.34
    assert r1['is_compliant'] is True
    assert r1['discrepancy_amount'] == 0.0

    # 2. Values only slash-separated block
    r2 = audit_unit_sale_price(
        mrp_val=20,
        quantity_magnitude=58.0,
        quantity_unit='g',
        declared_usp_str='2.9/BP3 01H6^^/0.34'
    )
    assert r2['declared_usp_numeric'] == 0.34
    assert r2['is_compliant'] is True

    # 3. Truncated first column with full block in context
    r3 = audit_unit_sale_price(
        mrp_val='20.00',
        quantity_magnitude=58.0,
        quantity_unit='g',
        declared_usp_str='PER g: 2.9',
        context_text='mrp: Rs 20.00 coding: ##NS/BN/ ₹ PER g: 2.9/BP3 01H6^^/0.34'
    )
    assert r3['declared_usp_numeric'] == 0.34
    assert r3['is_compliant'] is True

    # 4. Completely missing USP under amended 2021 rules
    r4 = audit_unit_sale_price(
        mrp_val='20.00',
        quantity_magnitude=58.0,
        quantity_unit='g',
        declared_usp_str=None
    )
    assert r4['is_compliant'] is False
    assert any('Rule 6(1)(e)' in v for v in r4['violations'])

def test_pdf_and_docx_report_generation_all_sections():
    mock_payload = {
        'id': 'scan-test-12345678',
        'created_at': None,
        'product_name': 'Bingo Mad Angles Achaari Masti',
        'category': 'Snack Foods',
        'inspector_name': 'Inspector Sharma',
        'reference_scale_mm': 25.0,
        'overall_compliance_verdict': 'COMPLIANT',
        'compliance_score': 100.0,
        'rule_results': [
            {
                'rule_id': 'RULE_6_1_A',
                'clause_reference': 'Rule 6(1)(a)',
                'title': 'Manufacturer Identification & Factory Premises',
                'status': 'PASS',
                'extracted_value': 'ITC Limited, Plot 1, Sector 11, Haridwar, Uttarakhand - 249403',
                'remarks': 'Factory address resolved and verified.',
                'image_index': 0
            },
            {
                'rule_id': 'RULE_6_1_E_USP',
                'clause_reference': 'Rule 6(1)(e)',
                'title': 'Unit Sale Price (USP) Mathematical Cross-Verification',
                'status': 'PASS',
                'extracted_value': '₹ 0.34 per g',
                'remarks': 'USP matches calculated Rs. 0.34 per g.',
                'image_index': 0
            }
        ],
        'extracted_data': {
            'product_name': {'value': 'Bingo Mad Angles Achaari Masti', 'status': 'found', 'confidence': 0.99, 'validation_remarks': 'Principal display panel.'},
            'generic_name': {'value': 'Corn & Rice Snacks', 'status': 'found', 'confidence': 0.95, 'validation_remarks': 'Rule 6(1)(b) compliant.'},
            'manufacturer_name': {'value': 'ITC Limited', 'status': 'found', 'confidence': 0.98, 'validation_remarks': 'Rule 6(1)(a) verified.'},
            'manufacturer_address': {'value': 'Plot 1, Sector 11, Haridwar, Uttarakhand - 249403', 'status': 'found', 'confidence': 0.95, 'validation_remarks': 'Physical address verified.'},
            'net_quantity': {'value': '58 g', 'status': 'found', 'confidence': 0.99, 'validation_remarks': 'Rule 6(1)(c) SI unit verified.'},
            'mrp': {'value': '₹ 20.00 (incl. of all taxes)', 'status': 'found', 'confidence': 0.99, 'validation_remarks': 'Rule 6(1)(e) verified.'},
            'unit_sale_price': {'value': '₹ 0.34 per g', 'status': 'found', 'confidence': 0.95, 'validation_remarks': 'USP verified.'},
            'mfg_date': {'value': '01/2026', 'status': 'found', 'confidence': 0.95, 'validation_remarks': 'Rule 6(1)(d) verified.'},
            'consumer_care': {'value': '1800 425 4444 / itccares@itc.in', 'status': 'found', 'confidence': 0.95, 'validation_remarks': 'Rule 6(1)(f) verified.'},
            'country_of_origin': {'value': 'India', 'status': 'found', 'confidence': 0.99, 'validation_remarks': 'Rule 6(1)(g) verified.'}
        },
        'master_report': {
            'product_name': 'Bingo Mad Angles Achaari Masti',
            'usp_cross_verification': {
                'mrp_numeric': 20.0,
                'quantity_numeric': 58.0,
                'quantity_unit': 'g',
                'calculated_usp_per_base_unit': 0.3448,
                'calculated_usp_unit': 'Rs per g',
                'declared_usp_raw': '0.34',
                'declared_usp_numeric': 0.34,
                'is_mathematically_accurate': True,
                'is_compliant': True,
                'remarks': 'Unit Sale Price verified: Declared 0.34 matches calculated Rs per g (Rs. 0.34).'
            },
            'second_schedule_shrinkflation_audit': {
                'is_second_schedule_commodity': True,
                'matched_commodity_category': 'Biscuits & Snack Foods',
                'declared_quantity': '58 g',
                'nearest_standard_pack_size': '50 g',
                'shrinkage_percentage': 0.0,
                'is_compliant': True,
                'remarks': 'Standard pack size conforms to Second Schedule.'
            },
            'visual_and_metrology_audit': {
                'rule_7_font_size': {
                    'measured_numeral_height_mm': 2.5,
                    'statutory_min_height_mm': 1.0,
                    'is_compliant': True,
                    'remarks': 'Numeral height satisfies Table-I requirements.'
                },
                'rule_9_color_contrast': {
                    'contrast_ratio': 4.8,
                    'is_compliant': True,
                    'remarks': 'Background color contrast is conspicuous (> 3.0:1).'
                }
            },
            'statutory_summary': []
        },
        'cross_referenced_fields': ['mrp', 'mfg_or_pkd_date'],
        'image_urls': ['http://minio:9000/scans/sample1.jpg'],
        'inspector_notes': 'All declarations conspicuously legible.'
    }

    # Generate PDF
    pdf_bytes = pdf_report_generator.generate(mock_payload)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b'%PDF')

    # Generate DOCX
    docx_bytes = docx_report_generator.generate(mock_payload)
    assert len(docx_bytes) > 1000
    doc = Document(io.BytesIO(docx_bytes))
    headings = [p.text for p in doc.paragraphs if p.text]
    full_text = ' '.join(headings + [c.text for t in doc.tables for r in t.rows for c in r.cells])
    
    # Verify all 7 sections exist in DOCX
    assert 'Rule-by-Rule Compliance Checklist' in full_text
    assert 'Extracted Mandatory Declarations' in full_text
    assert 'Unit Sale Price (USP) Mathematical Cross-Verification' in full_text
    assert 'Second Schedule Prescribed Pack Sizes' in full_text
    assert 'Physical & Visual Metrology Audit' in full_text
    assert 'Table-I Numeral & Letter Height' in full_text
    assert '0.34' in full_text
    assert '58 g' in full_text
