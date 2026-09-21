import os
import pytest
from app.pipeline.multi_panel_scanner import (
    detect_all_qr_codes,
    detect_qr_code,
    AwaitingQREvidenceException,
    run_master_inspection,
    QRClassificationItem,
    PackagingQRClassificationReport
)

def test_detect_all_qr_codes_extracts_multiple():
    """Verify that detect_all_qr_codes inspects packaging and decodes optical QR codes."""
    sample_path = os.path.join(os.path.dirname(__file__), "..", "test_samples", "bingo_multi_qr.jpg")
    if not os.path.exists(sample_path):
        pytest.skip("bingo_multi_qr.jpg not found in test_samples")

    all_qrs = detect_all_qr_codes([sample_path])
    assert isinstance(all_qrs, list)
    assert len(all_qrs) >= 1
    found_urls = [q.get("resolved_url") or q.get("raw_url") for q in all_qrs]
    assert any("instagram" in u or "qrco.de" in u for u in found_urls)

def test_multi_qr_bingo_mad_angles_classification():
    """
    Verify that on the Bingo Mad Angles packaging:
    1. Marketing QR (Instagram) is filtered out.
    2. Compliance QR (FSSAI/manufacturer) is selected.
    3. AwaitingQREvidenceException is raised with compliance URL and available_compliance_qrs populated.
    """
    sample_path = os.path.join(os.path.dirname(__file__), "..", "test_samples", "bingo_multi_qr.jpg")
    if not os.path.exists(sample_path):
        pytest.skip("bingo_multi_qr.jpg not found in test_samples")

    with pytest.raises(AwaitingQREvidenceException) as exc_info:
        run_master_inspection([sample_path])

    qe = exc_info.value
    assert "instagram" not in (qe.detected_qr_url or "").lower()
    assert "qrco.de" not in (qe.detected_qr_url or "").lower()
    assert "bingosnacks.com" in (qe.detected_qr_url or "").lower()
    assert "factory-locator" in (qe.detected_qr_url or "").lower()

    assert len(qe.available_compliance_qrs) >= 1
    primary_qr = qe.available_compliance_qrs[0]
    nearby = primary_qr.get("nearby_text", "").upper()
    assert "BRAND OWNER" in nearby or "FSSAI" in nearby or "MANUFACTURING" in nearby
