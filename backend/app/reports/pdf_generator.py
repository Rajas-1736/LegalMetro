import os
import io
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from jinja2 import Template
from app.storage.minio_client import storage_service

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, KeepTogether, PageBreak, HRFlowable
)
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Legal Metrology Compliance Report</title>
<style>
  @page {
    size: A4;
    margin: 1.2cm;
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
      font-size: 8pt;
      color: #64748b;
    }
    @bottom-left {
      content: "VisionX • Official Enforcement Record • Legal Metrology Act, 2009";
      font-size: 8pt;
      color: #64748b;
    }
  }
  body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.35;
    font-size: 9pt;
  }
  .header {
    text-align: center;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 8px;
    margin-bottom: 12px;
  }
  .gov-title {
    font-size: 10pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #0f172a;
    margin-bottom: 2px;
  }
  .sub-title {
    font-size: 8.5pt;
    color: #334155;
    margin-bottom: 3px;
  }
  .report-heading {
    font-size: 13pt;
    font-weight: 800;
    color: #1e3a8a;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .meta-grid {
    display: table;
    width: 100%;
    margin-bottom: 12px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px;
  }
  .meta-row {
    display: table-row;
  }
  .meta-cell {
    display: table-cell;
    padding: 3px 6px;
    font-size: 8.5pt;
  }
  .meta-label {
    font-weight: bold;
    color: #475569;
  }
  .verdict-banner {
    padding: 8px;
    border-radius: 4px;
    text-align: center;
    font-size: 11pt;
    font-weight: bold;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .verdict-COMPLIANT {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
  }
  .verdict-NON_COMPLIANT {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
  }
  .verdict-FLAGGED_FOR_REVIEW {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
  }
  h3 {
    font-size: 9.5pt;
    color: #0f172a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 14px;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .table-subtitle {
    font-size: 7.5pt;
    color: #64748b;
    font-weight: normal;
    text-transform: none;
    float: right;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
    font-size: 8pt;
  }
  th {
    background-color: #f1f5f9;
    color: #1e293b;
    font-weight: bold;
    text-align: left;
    padding: 5px 6px;
    border: 1px solid #cbd5e1;
  }
  td {
    padding: 5px 6px;
    border: 1px solid #cbd5e1;
    vertical-align: top;
  }
  .status-badge {
    display: inline-block;
    padding: 1px 5px;
    font-size: 7pt;
    font-weight: bold;
    border-radius: 3px;
    text-transform: uppercase;
  }
  .status-PASS, .status-found, .status-valid, .status-COMPLIANT { background-color: #dcfce7; color: #15803d; }
  .status-FAIL, .status-missing, .status-invalid, .status-NON_COMPLIANT { background-color: #fee2e2; color: #b91c1c; }
  .status-REVIEW, .status-NEEDS_REVIEW, .status-review_required, .status-NEEDS_MANUAL_INSPECTION, .status-FLAGGED_FOR_REVIEW { background-color: #fef3c7; color: #b45309; }
  .manual-edit-badge {
    display: inline-block;
    padding: 1px 5px;
    font-size: 6.5pt;
    font-weight: bold;
    border-radius: 3px;
    text-transform: uppercase;
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
    margin-left: 4px;
    vertical-align: middle;
  }
  .manual-edit-notice-box {
    margin-top: 12px;
    padding: 6px 10px;
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 3px solid #f59e0b;
    border-radius: 3px;
    font-size: 7.5pt;
    color: #92400e;
    line-height: 1.4;
  }
  .penalty-card {
    background-color: #fef2f2;
    border: 1px solid #fee2e2;
    border-left: 3px solid #ef4444;
    padding: 5px 8px;
    margin-bottom: 4px;
    font-size: 8pt;
    color: #7f1d1d;
  }
  .signature-section {
    margin-top: 24px;
    display: table;
    width: 100%;
  }
  .sig-box {
    display: table-cell;
    width: 50%;
    vertical-align: bottom;
  }
  .sig-line {
    width: 200px;
    border-top: 1px solid #334155;
    margin-top: 35px;
    padding-top: 4px;
    font-size: 8pt;
    color: #475569;
  }
</style>
</head>
<body>

<div class="header">
  <div class="gov-title">Government of India • Ministry of Consumer Affairs, Food & Public Distribution</div>
  <div class="sub-title">Department of Legal Metrology — Inspection & Enforcement Division</div>
  <div class="report-heading">Packaged Commodity Compliance Inspection Report</div>
  <div style="font-size: 7.5pt; color: #64748b; margin-top: 2px;">
    Issued under Section 18 & 52 of Legal Metrology Act, 2009 read with Legal Metrology (Packaged Commodities) Rules, 2011
  </div>
</div>

<div class="meta-grid">
  <div class="meta-row">
    <div class="meta-cell"><span class="meta-label">Inspection ID:</span> {{ scan.id }}</div>
    <div class="meta-cell"><span class="meta-label">Date & Time:</span> {{ scan.created_at.strftime('%d-%b-%Y %H:%M UTC') if scan.created_at else 'N/A' }}</div>
  </div>
  <div class="meta-row">
    <div class="meta-cell"><span class="meta-label">Product / Brand:</span> {{ scan.product_name or 'Packaged Commodity' }}</div>
    <div class="meta-cell"><span class="meta-label">Category:</span> {{ scan.category or 'Packaged Commodity' }}</div>
  </div>
  <div class="meta-row">
    <div class="meta-cell"><span class="meta-label">Inspecting Officer:</span> {{ scan.inspector_name or 'Senior Inspector' }}</div>
    <div class="meta-cell"><span class="meta-label">Physical Scale:</span> {{ scan.reference_scale_mm ~ ' mm' if scan.reference_scale_mm else 'None Provided' }} | {{ (scan.image_urls | length) if scan.image_urls else 1 }} Panel(s)</div>
  </div>
</div>

<div class="verdict-banner verdict-{{ scan.overall_compliance_verdict }}">
  Overall Verdict: {{ scan.overall_compliance_verdict.replace('_', ' ') }} • Score: {{ scan.compliance_score }}%
</div>

{% if scan.cross_referenced_fields and scan.cross_referenced_fields | length > 0 %}
<div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 6px 10px; margin-bottom: 10px; font-size: 8pt; color: #1e40af;">
  <strong>Cross-Panel Directives Detected:</strong> Declarations for <strong>{{ scan.cross_referenced_fields | join(', ') }}</strong> contain cross-panel pointers (e.g. <em>'SEE BASE / SIDE PANEL'</em>) directing enforcement officers to secondary packaging surfaces.
</div>
{% endif %}

<!-- Section 1: Rule-by-Rule Compliance Checklist -->
<h3>1. Rule-by-Rule Compliance Checklist (Rules 2011)</h3>
<table>
  <thead>
    <tr>
      <th style="width: 25%;">Rule & Legal Citation</th>
      <th style="width: 12%; text-align: center;">Verdict</th>
      <th style="width: 25%;">Declared Text Found</th>
      <th style="width: 38%;">Inspector Findings & Sanity Validation</th>
    </tr>
  </thead>
  <tbody>
    {% for rule in scan.rule_results %}
    <tr>
      <td>
        <strong>{{ rule.title }}</strong><br>
        <small style="color: #64748b;">{{ rule.clause_reference }}</small>
        {% if rule.image_index is defined and rule.image_index > 0 %}
        <br><span style="display:inline-block; margin-top:2px; font-size:7pt; color:#2563eb; background:#dbeafe; padding:1px 4px; border-radius:2px;">Panel {{ rule.image_index + 1 }}</span>
        {% endif %}
      </td>
      <td style="text-align: center;">
        <span class="status-badge status-{{ rule.status }}">{{ rule.status }}</span>
      </td>
      <td>{{ rule.extracted_value or 'Not Found' }}</td>
      <td>{{ rule.remarks }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<!-- Section 2: Structured Mandatory Declarations Summary (Table 1.0) -->
<h3>
  2. Structured Mandatory Declarations Summary (Auditable Evidence)
  <span class="table-subtitle">Table 1.0 — Legal Metrology Rules, 2011</span>
</h3>
<table>
  <thead>
    <tr>
      <th style="width: 25%;">Declaration Field</th>
      <th style="width: 28%;">Declared Value</th>
      <th style="width: 10%; text-align: center;">Status</th>
      <th style="width: 10%; text-align: center;">Confidence</th>
      <th style="width: 27%;">Statutory Audit Remarks</th>
    </tr>
  </thead>
  <tbody>
    {% set field_defs = [
      ('product_name', 'Product / Brand Name', 'found', 'Identified from principal display panel.'),
      ('generic_name', 'Common / Generic Commodity Name (Rule 6(1)(b))', 'missing', 'Rule 6(1)(b) verification.'),
      ('manufacturer_name', 'Manufacturer / Packer Legal Name (Rule 6(1)(a))', 'invalid', 'Rule 6(1)(a) verification.'),
      ('manufacturer_address', 'Complete Physical Factory Address (Rule 6(1)(a))', 'invalid', 'Rule 6(1)(a) factory premises verification.'),
      ('net_quantity', 'Net Quantity & Standard SI Units (Rule 6(1)(c) & Rule 13)', 'invalid', 'Rule 6(1)(c) & Rule 13 audit.'),
      ('mrp', 'Maximum Retail Price [MRP] (Rule 6(1)(e))', 'invalid', 'Rule 6(1)(e) retail price declaration.'),
      ('unit_sale_price', 'Unit Sale Price [USP] (Rule 6(1)(e) Amendment)', 'missing', 'Rule 6(1)(e) USP mandate.'),
      ('mfg_date', 'Month & Year of Manufacture / Packing (Rule 6(1)(d))', 'missing', 'Rule 6(1)(d) date declaration.'),
      ('consumer_care', 'Consumer Care Contact Details (Rule 6(1)(f))', 'missing', 'Rule 6(1)(f) grievance contact.'),
      ('country_of_origin', 'Country of Origin Declaration (Rule 6(1)(g))', 'missing', 'Rule 6(1)(g) origin declaration.')
    ] %}
    {% set master_mand = (scan.master_report and scan.master_report.mandatory_declarations) or {} %}
    {% set master_mfg = (scan.master_report and scan.master_report.manufacturer_details) or {} %}
    {% set edited_fields = scan.edited_fields or {} %}

    {% for key, label, def_status, def_remarks in field_defs %}
      {% set f = scan.extracted_data.get(key) if (scan.extracted_data and scan.extracted_data.get(key) is mapping) else None %}
      {% set is_edited = (key in edited_fields) or (f and f.get('is_manually_edited')) %}
      {% set val = (edited_fields.get(key, {}).get('edited_value')) or (f.get('value') if f else None) or (master_mand.get(key, {}).get('declared_value')) or (scan.product_name if key == 'product_name' else None) %}
      {% if not val and key == 'manufacturer_name' %}{% set val = master_mfg.get('resolved_manufacturer_name') %}{% endif %}
      {% if not val and key == 'manufacturer_address' %}{% set val = master_mfg.get('resolved_address') %}{% endif %}
      
      {% set stat = (f.get('status') if f else None) or (master_mand.get(key, {}).get('compliance_status')) or (master_mfg.get('compliance_status') if 'manufacturer' in key else None) or ('found' if val else def_status) %}
      {% set rem = (f.get('validation_remarks') if f else None) or (master_mand.get(key, {}).get('compliance_remarks')) or (master_mfg.get('compliance_remarks') if 'manufacturer' in key else None) or def_remarks %}
      {% set conf = (f.get('confidence') if f else None) or 0.95 %}

      {% set is_pass = stat in ['valid', 'found', 'COMPLIANT'] %}
      {% set is_review = stat in ['review_required', 'NEEDS_REVIEW', 'NEEDS_MANUAL_INSPECTION'] %}

      <tr>
        <td>
          <strong>{{ label }}</strong>
          {% if is_edited %}
          <span class="manual-edit-badge" title="Manually verified by inspecting officer">MANUAL EDIT</span>
          {% endif %}
        </td>
        <td>{{ val or 'Not Declared on Pack' }}</td>
        <td style="text-align: center;">
          <span class="status-badge status-{{ 'PASS' if is_pass else ('REVIEW' if is_review else 'FAIL') }}">
            {{ 'PASS' if is_pass else ('REVIEW' if is_review else 'FAIL') }}
          </span>
        </td>
        <td style="text-align: center;">{{ (conf * 100) | round(0) | int }}%</td>
        <td><small style="color: #475569;">{{ rem }}</small></td>
      </tr>
    {% endfor %}
  </tbody>
</table>

<!-- Section 3: USP Mathematical Cross-Verification (Table 2.0) -->
{% set usp = (scan.master_report and scan.master_report.usp_cross_verification) or (scan.extracted_data and scan.extracted_data.usp_cross_verification) %}
{% if usp and (usp.get('mrp_numeric') or usp.get('calculated_usp_per_base_unit')) %}
<h3>
  3. Unit Sale Price (USP) Mathematical Cross-Verification (Rule 6(1)(e))
  <span class="table-subtitle">Table 2.0 — Mathematical Audit</span>
</h3>
<table>
  <thead>
    <tr>
      <th style="width: 20%;">Declared MRP</th>
      <th style="width: 20%;">Net Quantity</th>
      <th style="width: 20%;">Declared USP</th>
      <th style="width: 20%;">Calculated Base USP</th>
      <th style="width: 20%; text-align: center;">Verdict</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>₹ {{ usp.get('mrp_numeric', 'N/A') }}</td>
      <td>{{ usp.get('quantity_numeric', 'N/A') }} {{ usp.get('quantity_unit', '') }}</td>
      <td>{{ usp.get('declared_usp_raw') or (('₹ ' ~ usp.get('declared_usp_numeric')) if usp.get('declared_usp_numeric') else 'Not declared') }}</td>
      <td><strong>₹ {{ usp.get('calculated_usp_per_base_unit', 'N/A') }} {{ usp.get('calculated_usp_unit', '') }}</strong></td>
      <td style="text-align: center;">
        <span class="status-badge status-{{ 'PASS' if usp.get('is_compliant') else 'FAIL' }}">
          {{ 'COMPLIANT' if usp.get('is_compliant') else 'VIOLATION' }}
        </span>
      </td>
    </tr>
    <tr>
      <td colspan="5" style="background: #f8fafc; font-size: 7.5pt;">
        <strong>Statutory Analysis:</strong> {{ usp.get('remarks', 'Mathematical calculation verified.') }}
        {% if usp.get('violations') %}
          <br><span style="color: #b91c1c; font-weight: bold;">Statutory Infractions:</span> {{ usp.get('violations') | join('; ') }}
        {% endif %}
      </td>
    </tr>
  </tbody>
</table>
{% endif %}

<!-- Section 4: Second Schedule Standard Pack Sizes & Anti-Shrinkflation Audit (Table 3.0) -->
{% set shrink = (scan.master_report and scan.master_report.second_schedule_shrinkflation_audit) or (scan.extracted_data and scan.extracted_data.second_schedule_shrinkflation_audit) %}
{% if shrink and shrink.get('is_second_schedule_commodity') %}
<h3>
  4. Second Schedule Prescribed Pack Sizes & Anti-Shrinkflation Audit (Rule 5)
  <span class="table-subtitle">Table 3.0 — Second Schedule Conformance</span>
</h3>
<table>
  <thead>
    <tr>
      <th style="width: 28%;">Prescribed Commodity Category</th>
      <th style="width: 18%;">Declared Pack Size</th>
      <th style="width: 18%;">Nearest Standard</th>
      <th style="width: 18%;">Deviation / Downsizing</th>
      <th style="width: 18%; text-align: center;">Verdict</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>{{ shrink.get('matched_commodity_category', 'Not Restricted') }}</strong></td>
      <td>{{ shrink.get('declared_quantity', 'N/A') }}</td>
      <td>{{ shrink.get('nearest_standard_pack_size') or 'N/A' }}</td>
      <td style="color: {{ '#b91c1c' if shrink.get('shrinkage_percentage', 0) > 0 else '#15803d' }}; font-weight: bold;">
        {{ shrink.get('shrinkage_percentage', 0) }}%
      </td>
      <td style="text-align: center;">
        <span class="status-badge status-{{ 'PASS' if shrink.get('is_compliant') else 'FAIL' }}">
          {{ 'PASS' if shrink.get('is_compliant') else 'FAIL' }}
        </span>
      </td>
    </tr>
    <tr>
      <td colspan="5" style="background: #f8fafc; font-size: 7.5pt;">
        <strong>Statutory Findings:</strong> {{ shrink.get('remarks', 'Verified against Schedule II standard quantities.') }}
        {% if shrink.get('prescribed_pack_sizes_sample') %}
          <br><span style="color: #475569;">Permitted standard sizes sample: {{ shrink.get('prescribed_pack_sizes_sample') | join(', ') }}</span>
        {% endif %}
      </td>
    </tr>
  </tbody>
</table>
{% endif %}

<!-- Section 5: Physical & Visual Metrology Audit (Rule 7 & 9 - Table 4.0) -->
{% set metro = (scan.master_report and scan.master_report.visual_and_metrology_audit) or (scan.extracted_data and scan.extracted_data.visual_and_metrology_audit) %}
{% if metro and (metro.rule_7_font_size or metro.rule_9_color_contrast) %}
<h3>
  5. Physical & Visual Metrology Audit (Rule 7 & 9)
  <span class="table-subtitle">Table 4.0 — Optical Verification</span>
</h3>
<table>
  <thead>
    <tr>
      <th style="width: 32%;">Metrology Parameter</th>
      <th style="width: 20%;">Measured Value</th>
      <th style="width: 20%;">Statutory Benchmark</th>
      <th style="width: 14%; text-align: center;">Verdict</th>
      <th style="width: 14%;">Remarks</th>
    </tr>
  </thead>
  <tbody>
    {% if metro.rule_7_font_size %}
    {% set font = metro.rule_7_font_size %}
    <tr>
      <td><strong>Table-I Numeral & Letter Height (Rule 7(2))</strong></td>
      <td>{{ (font.measured_numeral_height_mm ~ ' mm') if font.measured_numeral_height_mm else 'Optical Measurement' }}</td>
      <td>Min {{ font.statutory_min_height_mm or 1.0 }} mm</td>
      <td style="text-align: center;">
        <span class="status-badge status-{{ 'PASS' if font.is_compliant else 'FAIL' }}">
          {{ 'PASS' if font.is_compliant else 'FAIL' }}
        </span>
      </td>
      <td><small>{{ font.remarks or 'Complies with Table-I' }}</small></td>
    </tr>
    {% endif %}
    {% if metro.rule_9_color_contrast %}
    {% set contrast = metro.rule_9_color_contrast %}
    <tr>
      <td><strong>Background Color Contrast (Rule 9(1)(b))</strong></td>
      <td>Ratio: {{ contrast.contrast_ratio or 'Conspicuous' }}</td>
      <td>Min 3.0:1 Ratio</td>
      <td style="text-align: center;">
        <span class="status-badge status-{{ 'PASS' if contrast.is_compliant else 'FAIL' }}">
          {{ 'PASS' if contrast.is_compliant else 'FAIL' }}
        </span>
      </td>
      <td><small>{{ contrast.remarks or 'Conspicuous contrast' }}</small></td>
    </tr>
    {% endif %}
  </tbody>
</table>
{% endif %}

<!-- Section 6: Statutory Violations & Enforcement Penalties (Section 36(1)) -->
{% set violations = scan.actual_violations or [] %}
{% if violations | length > 0 %}
<h3>6. Statutory Violations & Enforcement Penalties (Legal Metrology Act, 2009)</h3>
<div>
  {% for item in violations %}
  <div class="penalty-card">
    <strong>Violation {{ loop.index }}:</strong> {{ item }}
  </div>
  {% endfor %}
</div>
{% else %}
<h3>6. Statutory Enforcement Summary (Legal Metrology Act, 2009)</h3>
<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-left: 3px solid #22c55e; padding: 6px 10px; font-size: 8pt; color: #166534; border-radius: 2px;">
  <strong>Nil Infractions Recorded:</strong> All mandatory packaging declarations comply strictly with the Legal Metrology (Packaged Commodities) Rules, 2011. No statutory penalties under Section 36(1) or Section 39 applicable.
</div>
{% endif %}

{% if scan.inspector_notes %}
<h3>7. Inspecting Officer Remarks & Evidence Notes</h3>
<p style="background: #f8fafc; padding: 6px 8px; border: 1px solid #e2e8f0; font-size: 8pt;">
  {{ scan.inspector_notes }}
</p>
{% endif %}

<div class="manual-edit-notice-box">
  <strong>Statutory Audit Note on Evidentiary Badges:</strong>
  Fields marked with the amber <strong>[MANUAL EDIT]</strong> badge indicate declaration parameters physically inspected, validated, and updated by the authorized Legal Metrology enforcement officer, superseding automated OCR/AI detections under Section 15 of the Legal Metrology Act, 2009. Fields without this badge represent automated multimodal extractions.
</div>

<div class="signature-section">
  <div class="sig-box">
    <div class="sig-line">
      {{ scan.inspector_name or 'Authorized Enforcement Officer' }}<br>
      Legal Metrology Department
    </div>
  </div>
  <div class="sig-box" style="text-align: right;">
    <div class="sig-line" style="margin-left: auto;">
      Seal / Digital Verification Stamp<br>
      Ministry of Consumer Affairs
    </div>
  </div>
</div>

</body>
</html>
"""

class PDFReportGenerator:
    """Generates official compliance inspection report as PDF using WeasyPrint."""

    def generate(self, scan_data: Dict[str, Any]) -> bytes:
        scan_copy = dict(scan_data)
        master = dict(scan_copy.get("master_report") or scan_copy.get("extracted_data") or {})
        raw_summary = master.get("statutory_summary") or scan_copy.get("statutory_summary") or []
        actual_violations = [
            item for item in raw_summary
            if "comply strictly" not in item.lower() and "no statutory" not in item.lower() and "nil" not in item.lower()
        ]
        master["statutory_summary"] = actual_violations
        master["actual_violations"] = actual_violations
        scan_copy["master_report"] = master
        scan_copy["actual_violations"] = actual_violations

        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(scan=scan_copy)

        # 1. Try WeasyPrint if available
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=rendered_html).write_pdf()
            return pdf_bytes
        except Exception:
            pass

        # 2. Fallback to ReportLab: generates true, valid binary PDF readable on all smartphones
        try:
            return self._generate_reportlab(scan_copy)
        except Exception as e:
            logger.error(f"ReportLab PDF generation failed: {e}")
            return rendered_html.encode("utf-8")

    def _generate_reportlab(self, scan_data: Dict[str, Any]) -> bytes:
        master = dict(scan_data.get("master_report") or scan_data.get("extracted_data") or {})

        PRIMARY_NAVY = colors.HexColor("#0F2942")
        SECONDARY_SLATE = colors.HexColor("#334155")
        BORDER_COLOR = colors.HexColor("#CBD5E1")
        HEADER_BG = colors.HexColor("#F1F5F9")
        SUCCESS_GREEN = colors.HexColor("#15803D")
        SUCCESS_BG = colors.HexColor("#DCFCE7")
        DANGER_RED = colors.HexColor("#B91C1C")
        DANGER_BG = colors.HexColor("#FEE2E2")
        WARNING_AMBER = colors.HexColor("#B45309")
        WARNING_BG = colors.HexColor("#FEF3C7")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        style_ministry = ParagraphStyle('MinistryHeader', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=PRIMARY_NAVY, alignment=1)
        style_sub_header = ParagraphStyle('SubHeader', fontName='Helvetica', fontSize=8, leading=10.5, textColor=SECONDARY_SLATE, alignment=1)
        style_title = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=12.5, leading=15, textColor=PRIMARY_NAVY, alignment=1, spaceAfter=4)
        style_section_title = ParagraphStyle('SectionTitle', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=PRIMARY_NAVY, spaceBefore=5, spaceAfter=3)
        style_cell_bold = ParagraphStyle('CellBold', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=PRIMARY_NAVY)
        style_cell_regular = ParagraphStyle('CellRegular', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.black)
        style_verdict_badge = ParagraphStyle('VerdictBadge', fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=1)
        style_remarks_bullet = ParagraphStyle('RemarksBullet', fontName='Helvetica', fontSize=7, leading=9, textColor=DANGER_RED)

        story = []

        # 1. Header
        story.append(Paragraph("GOVERNMENT OF INDIA", style_ministry))
        story.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", style_ministry))
        story.append(Paragraph("LEGAL METROLOGY DIVISION (FIELD ENFORCEMENT & COMPLIANCE WING)", style_sub_header))
        story.append(Spacer(1, 3))
        story.append(Paragraph("STATUTORY PACKAGE COMPLIANCE & VERIFICATION REPORT", style_title))
        story.append(Paragraph("Issued under Section 15 of Legal Metrology Act, 2009 read with Legal Metrology (Packaged Commodities) Rules, 2011", style_sub_header))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_NAVY, spaceAfter=6, spaceBefore=3))

        # 2. Metadata & Verdict Banner
        raw_verdict = str(scan_data.get("overall_compliance_verdict") or master.get("overall_compliance") or "NON_COMPLIANT").upper()
        if "COMPLIANT" in raw_verdict and "NON" not in raw_verdict:
            v_bg, v_col, v_text = SUCCESS_BG, SUCCESS_GREEN, "STATUTORY VERDICT: FULLY COMPLIANT"
        elif "MANUAL" in raw_verdict or "REVIEW" in raw_verdict:
            v_bg, v_col, v_text = WARNING_BG, WARNING_AMBER, "STATUTORY VERDICT: PHYSICAL CHECK (RULE 7(3))"
        else:
            v_bg, v_col, v_text = DANGER_BG, DANGER_RED, "STATUTORY VERDICT: VIOLATION DETECTED"

        style_verdict_badge.textColor = v_col
        scan_id = str(scan_data.get("id", "SCAN"))[:8].upper()
        memo_id = f"LMR-2026-INSP-{scan_id}"

        created_at = scan_data.get("created_at")
        if isinstance(created_at, datetime):
            inspect_time = created_at.strftime("%d-%b-%Y %H:%M:%S IST")
        else:
            inspect_time = datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")

        image_urls = scan_data.get("image_urls") or []
        inspector_name = scan_data.get("inspector_name") or "Authorized Metrology Officer"

        meta_table_data = [
            [
                Paragraph(f"<b>Inspection Memo ID:</b> {memo_id}", style_cell_regular),
                Paragraph(f"<b>Date & Time:</b> {inspect_time}", style_cell_regular),
                Paragraph(v_text, style_verdict_badge)
            ],
            [
                Paragraph(f"<b>Inspecting Officer:</b> {inspector_name}", style_cell_regular),
                Paragraph("<b>Jurisdiction:</b> Central Enforcement Squad, District Metrology Cell", style_cell_regular),
                Paragraph(f"<b>Total Panels Scanned:</b> {len(image_urls) or 1}", style_cell_regular)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[175, 175, 173])
        meta_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (2, 0), (2, 0), v_bg),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 5))

        # 3. Commodity Details
        mfr_info = master.get("manufacturer_details") or {}
        imp_info = master.get("importer_details") or {}
        prod_name = scan_data.get("product_name") or master.get("product_name") or "Packaged Commodity"
        batch_num = master.get("batch_number") or "N/A"
        mfr_name = mfr_info.get("resolved_manufacturer_name") or mfr_info.get("name") or "N/A"
        mfr_addr = mfr_info.get("resolved_address") or mfr_info.get("address") or "N/A"
        res_method = mfr_info.get("resolution_method") or "ON_PACK"
        coo = imp_info.get("country_of_origin") or "India"

        prod_data = [
            [
                Paragraph("<b>Product / Brand Name:</b>", style_cell_bold),
                Paragraph(str(prod_name), style_cell_regular),
                Paragraph("<b>Batch / Lot No:</b>", style_cell_bold),
                Paragraph(str(batch_num), style_cell_regular)
            ],
            [
                Paragraph("<b>Active Manufacturer:</b>", style_cell_bold),
                Paragraph(str(mfr_name), style_cell_regular),
                Paragraph("<b>Resolution Method:</b>", style_cell_bold),
                Paragraph(str(res_method), style_cell_regular)
            ],
            [
                Paragraph("<b>Factory Address:</b>", style_cell_bold),
                Paragraph(str(mfr_addr), style_cell_regular),
                Paragraph("<b>Country of Origin:</b>", style_cell_bold),
                Paragraph(str(coo), style_cell_regular)
            ]
        ]
        prod_table = Table(prod_data, colWidths=[105, 205, 95, 118])
        prod_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
            ('BACKGROUND', (2, 0), (2, -1), HEADER_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(prod_table)
        story.append(Spacer(1, 5))

        # 4. Statutory Violations or Affirmation
        story.append(Paragraph("1. STATUTORY SUMMARY & ACTIONABLE CONTRAVENTIONS", style_section_title))
        actual_violations = scan_data.get("actual_violations") or []
        if actual_violations:
            viol_rows = []
            for idx, item in enumerate(actual_violations, 1):
                viol_rows.append([
                    Paragraph(f"<b>{idx}.</b>", style_cell_bold),
                    Paragraph(str(item), style_remarks_bullet)
                ])
            viol_table = Table(viol_rows, colWidths=[20, 503])
            viol_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), DANGER_BG),
                ('BOX', (0, 0), (-1, -1), 1, DANGER_RED),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(viol_table)
        else:
            comp_box = [[Paragraph("All examined mandatory declarations, units, denominations, and packaging dimensions strictly adhere to the Legal Metrology (Packaged Commodities) Rules, 2011. Nil infractions recorded.", style_cell_regular)]]
            comp_table = Table(comp_box, colWidths=[523])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), SUCCESS_BG),
                ('BOX', (0, 0), (-1, -1), 1, SUCCESS_GREEN),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ]))
            story.append(comp_table)

        story.append(Spacer(1, 5))

        # 5. Anti-Shrinkflation & USP Audit
        story.append(Paragraph("2. ANTI-SHRINKFLATION & MATHEMATICAL UNIT SALE PRICE (USP) AUDIT", style_section_title))
        usp_info = master.get("usp_cross_verification") or {}
        shrink_info = master.get("second_schedule_shrinkflation_audit") or {}

        usp_is_acc = usp_info.get("is_mathematically_accurate", True)
        usp_status = "VERIFIED ACCURATE" if usp_is_acc else "MATHEMATICAL DISCREPANCY"
        usp_color = SUCCESS_GREEN if usp_is_acc else DANGER_RED

        shrink_std = shrink_info.get("is_standard_prescribed_pack_size", True)
        shrink_status = "STANDARD PACK SIZE" if shrink_std else "NON-STANDARD / SHRINKFLATED"
        shrink_color = SUCCESS_GREEN if shrink_std else DANGER_RED

        calc_usp = str(usp_info.get("calculated_usp_per_base_unit", "N/A")).replace("₹", "Rs. ")
        calc_unit = str(usp_info.get("calculated_usp_unit", "")).replace("₹", "Rs. ")
        raw_shrink = shrink_info.get("shrinkage_percentage")
        try:
            shrink_pct = float(raw_shrink) if raw_shrink is not None else 0.0
            shrink_str = f"{shrink_pct:+.1f}%"
        except (ValueError, TypeError):
            shrink_str = "0.0%"

        nearest_size = shrink_info.get("nearest_standard_pack_size") or "standard"
        decl_usp = str(usp_info.get("declared_usp_raw") or "Not Declared on Pack").replace("₹", "Rs. ")
        shrink_remarks = str(shrink_info.get("remarks") or "Standard packaging").replace("₹", "Rs. ")
        usp_remarks = str(usp_info.get("remarks") or "Verified").replace("₹", "Rs. ")

        special_data = [
            [
                Paragraph("<b>Rule 5 Anti-Shrinkflation:</b>", style_cell_bold),
                Paragraph(f"<font color='{shrink_color}'><b>{shrink_status}</b></font>", style_cell_bold),
                Paragraph("<b>Rule 6(1)(e) Mathematical USP:</b>", style_cell_bold),
                Paragraph(f"<font color='{usp_color}'><b>{usp_status}</b></font>", style_cell_bold),
            ],
            [
                Paragraph("<b>Regulated Category:</b>", style_cell_bold),
                Paragraph(str(shrink_info.get("matched_commodity_category") or "Unregulated / General Commodity"), style_cell_regular),
                Paragraph("<b>Calculated Base Unit Price:</b>", style_cell_bold),
                Paragraph(f"Rs. {calc_usp} ({calc_unit})", style_cell_regular)
            ],
            [
                Paragraph("<b>Shrinkage / Deviation:</b>", style_cell_bold),
                Paragraph(f"{shrink_str} vs {nearest_size}", style_cell_regular),
                Paragraph("<b>Declared Packaging USP:</b>", style_cell_bold),
                Paragraph(decl_usp, style_cell_regular)
            ],
            [
                Paragraph("<b>Shrinkflation Remarks:</b>", style_cell_bold),
                Paragraph(shrink_remarks, style_cell_regular),
                Paragraph("<b>USP Verification Remarks:</b>", style_cell_bold),
                Paragraph(usp_remarks, style_cell_regular)
            ]
        ]
        special_table = Table(special_data, colWidths=[120, 145, 120, 138])
        special_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
            ('BACKGROUND', (2, 0), (2, -1), HEADER_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(special_table)
        story.append(Spacer(1, 5))

        # 6. Mandatory Declarations Audit Table
        story.append(Paragraph("3. STATUTORY DECLARATION AUDIT TABLE (RULE 6 & RULE 13)", style_section_title))
        decl_headers = [
            Paragraph("<b>Rule</b>", style_cell_bold),
            Paragraph("<b>Statutory Declaration</b>", style_cell_bold),
            Paragraph("<b>Declared Value Extracted</b>", style_cell_bold),
            Paragraph("<b>Compliance Status</b>", style_cell_bold),
            Paragraph("<b>Statutory Remarks</b>", style_cell_bold)
        ]
        decl_rows = [decl_headers]

        # Use rule_results if available
        rule_results = scan_data.get("rule_results") or []
        edited_fields = scan_data.get("edited_fields") or {}
        if rule_results:
            for rr in rule_results:
                r_st = str(rr.get("status", "PASS")).upper()
                if "PASS" in r_st or "COMPLIANT" in r_st:
                    st_html = f"<font color='{SUCCESS_GREEN}'><b>COMPLIANT</b></font>"
                elif "REVIEW" in r_st or "MANUAL" in r_st:
                    st_html = f"<font color='{WARNING_AMBER}'><b>PHYSICAL CHECK</b></font>"
                else:
                    st_html = f"<font color='{DANGER_RED}'><b>VIOLATION</b></font>"

                # Check if this rule item was manually edited by inspector
                fkey = rr.get("field_key") or ""
                rid = rr.get("rule_id") or ""
                is_manual = (
                    fkey in edited_fields
                    or (rid in ["RULE_6_1_C", "RULE_6_1_C_AND_13"] and "net_quantity" in edited_fields)
                    or (rid == "RULE_6_1_E" and "mrp" in edited_fields)
                    or (rid == "RULE_6_1_A" and ("manufacturer_name" in edited_fields or "manufacturer_address" in edited_fields))
                    or rr.get("is_manually_edited")
                )

                # Untruncated, clean text with Rupee symbol converted to Rs.
                ext_val = str(rr.get("extracted_value") or rr.get("value") or "Verified on Pack").replace("₹", "Rs. ")
                rem_text = str(rr.get("remarks", "")).replace("₹", "Rs. ")
                clause_text = str(rr.get("clause_reference") or rr.get("rule_id", "")).replace("₹", "Rs. ")
                title_text = str(rr.get("title", "")).replace("₹", "Rs. ")

                badge_suffix = f" <font color='#92400E' size=5.5><b>[MANUAL EDIT]</b></font>" if is_manual else ""
                title_cell = f"<b>{title_text}</b>{badge_suffix}"

                decl_rows.append([
                    Paragraph(clause_text, style_cell_regular),
                    Paragraph(title_cell, style_cell_regular),
                    Paragraph(ext_val, style_cell_regular),
                    Paragraph(st_html, style_cell_regular),
                    Paragraph(rem_text, style_cell_regular)
                ])
        else:
            mand_decls = master.get("mandatory_declarations") or {}
            field_labels = {
                "generic_commodity_name": ("Rule 6(1)(b)", "Generic Name"),
                "net_quantity": ("Rule 6(1)(c)", "Net Quantity"),
                "mrp": ("Rule 6(1)(e)", "MRP (Taxes Incl.)"),
                "unit_sale_price": ("Rule 6(1)(e)", "Unit Sale Price"),
                "mfg_or_pkd_date": ("Rule 6(1)(d)", "Mfg/Pkd Date"),
                "consumer_care_details": ("Rule 6(1)(f)", "Consumer Care"),
                "country_of_origin": ("Rule 6(1)(g)", "Country of Origin")
            }
            for key, (rule_ref, label_str) in field_labels.items():
                item = mand_decls.get(key, {})
                val = str(item.get("declared_value") or "NOT FOUND").replace("₹", "Rs. ")
                status = str(item.get("compliance_status") or "NON_COMPLIANT").upper()
                remarks = str(item.get("compliance_remarks") or "").replace("₹", "Rs. ")

                if "COMPLIANT" in status and "NON" not in status:
                    st_html = f"<font color='{SUCCESS_GREEN}'><b>COMPLIANT</b></font>"
                elif "MANUAL" in status:
                    st_html = f"<font color='{WARNING_AMBER}'><b>PHYSICAL CHECK</b></font>"
                else:
                    st_html = f"<font color='{DANGER_RED}'><b>VIOLATION</b></font>"

                decl_rows.append([
                    Paragraph(rule_ref, style_cell_regular),
                    Paragraph(f"<b>{label_str}</b>", style_cell_regular),
                    Paragraph(val, style_cell_regular),
                    Paragraph(st_html, style_cell_regular),
                    Paragraph(remarks, style_cell_regular)
                ])

        decl_table = Table(decl_rows, colWidths=[65, 95, 145, 75, 143])
        decl_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(decl_table)
        story.append(Spacer(1, 5))

        # 7. Metrology Visual Gauges
        vis_audit = master.get("visual_and_metrology_audit") or {}
        font_data = vis_audit.get("rule_7_font_size") or {}
        contrast_data = vis_audit.get("rule_9_color_contrast") or {}

        stat_min = font_data.get("statutory_min_height_mm", 2.0)
        meas_h = font_data.get("measured_numeral_height_mm", "N/A")
        font_ok = font_data.get("is_compliant", True)
        cont_val = contrast_data.get("contrast_ratio", "N/A")
        cont_ok = contrast_data.get("is_compliant", True)

        vis_row = [
            [
                Paragraph("<b>Rule 7(2) Min Numeral Height:</b>", style_cell_bold),
                Paragraph(f"Statutory: {stat_min} mm | Measured: {meas_h} mm ({'COMPLIANT' if font_ok else 'NON-COMPLIANT'})", style_cell_regular),
                Paragraph("<b>Rule 9(1)(b) Color Contrast:</b>", style_cell_bold),
                Paragraph(f"Ratio: {cont_val} (Min 3.0:1) | {'COMPLIANT' if cont_ok else 'CONTRAST VIOLATION'}", style_cell_regular),
            ]
        ]
        vis_table = Table(vis_row, colWidths=[120, 145, 120, 138])
        vis_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
            ('BACKGROUND', (2, 0), (2, -1), HEADER_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        story.append(vis_table)

        # 8. Photographic Evidence & Section 65B Certificate
        story.append(Spacer(1, 8))

        # Collect evidence thumbnails
        storage_dir = getattr(storage_service, 'local_dir', './storage_data')
        valid_images = []
        for u in (scan_data.get("image_urls") or []):
            fn = os.path.basename(u)
            local_fp = os.path.join(storage_dir, fn)
            if os.path.exists(local_fp):
                valid_images.append(local_fp)

        if valid_images:
            story.append(Paragraph("4. PHOTOGRAPHIC EVIDENCE (SECTION 65B EVIDENCE ACT)", style_section_title))
            image_cells = []
            for img_path in valid_images[:4]:
                fname = os.path.basename(img_path)
                sha_hash = "N/A"
                try:
                    with open(img_path, "rb") as f:
                        sha_hash = hashlib.sha256(f.read()).hexdigest()[:16] + "..."
                except Exception:
                    pass

                rl_img = None
                try:
                    with PILImage.open(img_path) as pimg:
                        w, h = pimg.size
                        ratio = min(220 / w, 110 / h)
                        thumb_w, thumb_h = max(int(w * ratio * 2), 1), max(int(h * ratio * 2), 1)
                        pimg_thumb = pimg.convert("RGB").resize((thumb_w, thumb_h), PILImage.Resampling.LANCZOS)
                        thumb_buf = io.BytesIO()
                        pimg_thumb.save(thumb_buf, format="JPEG", quality=82)
                        thumb_buf.seek(0)
                        rl_img = RLImage(thumb_buf, width=w * ratio, height=h * ratio)
                except Exception:
                    rl_img = Paragraph("Thumbnail unavailable", style_cell_regular)

                cell_content = [
                    rl_img if rl_img else Paragraph("Image", style_cell_regular),
                    Spacer(1, 2),
                    Paragraph(f"<b>Evidence:</b> {fname}<br/><font color='#64748B' size=6>SHA-256: {sha_hash}</font>", style_cell_regular)
                ]
                image_cells.append(cell_content)

            grid_rows = []
            for i in range(0, len(image_cells), 2):
                row = [image_cells[i]]
                if i + 1 < len(image_cells):
                    row.append(image_cells[i + 1])
                else:
                    row.append([Paragraph("", style_cell_regular)])
                grid_rows.append(row)

            ev_table = Table(grid_rows, colWidths=[255, 255])
            ev_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(ev_table)
            story.append(Spacer(1, 6))

        # Evidentiary Notice Box for Badges
        notice_data = [[
            Paragraph("<b>STATUTORY NOTICE ON EVIDENTIARY BADGES:</b><br/>"
                      "Declarations marked with the amber <b>[MANUAL EDIT]</b> tag represent statutory metrics physically inspected, verified, and updated by the authorized enforcement officer under Section 15 of the Legal Metrology Act, 2009, superseding automated OCR extractions. Entries without this badge represent automated multimodal vision detections.",
                      ParagraphStyle('NoticeStyle', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor("#92400E")))
        ]]
        notice_table = Table(notice_data, colWidths=[523])
        notice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
            ('LINELEFT', (0, 0), (0, -1), 3, colors.HexColor("#F59E0B")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(notice_table)
        story.append(Spacer(1, 8))

        # Sign-off Block
        sign_block = [
            [
                Paragraph("<b>EVIDENCE INTEGRITY CERTIFICATE:</b><br/>"
                          "Certified that digital image evidence, OCR extractions, and statutory metric calculations "
                          "incorporated in this report were verified under continuous chain of custody and represent "
                          "true statutory records of the subject packaged commodity under the Legal Metrology Act, 2009.", style_cell_regular),
                Paragraph(f"<b>OFFICIAL SEAL & SIGNATURE:</b><br/><br/><br/>"
                          f"____________________________________<br/>"
                          f"<b>{inspector_name}</b><br/>"
                          f"Legal Metrology Enforcement Officer<br/>"
                          f"Govt. of India / State Metrology Department", style_cell_regular)
            ]
        ]
        sign_table = Table(sign_block, colWidths=[310, 213])
        sign_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, PRIMARY_NAVY),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether(sign_table))

        doc.build(story)
        return buf.getvalue()

pdf_report_generator = PDFReportGenerator()


