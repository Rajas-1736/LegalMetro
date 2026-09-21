import requests
import time
import sys
import json

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    print("=== STEP 1: Logging in as Inspector ===")
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "inspector@legalmetro.gov.in", "password": "inspector123"}
    )
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code} {login_resp.text}")
        sys.exit(1)

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful! Token acquired.")

    print("\n=== STEP 2: Submitting scan job with imgqr.jpeg ===")
    with open("/app/test_samples/imgqr.jpeg", "rb") as f:
        files = [("images", ("imgqr.jpeg", f, "image/jpeg"))]
        data = {
            "product_name": "Masala Chana Dal Live Test",
            "category": "Packaged Food",
            "reference_scale_mm": 100.0,
            "inspector_notes": "Testing QR code workflow end-to-end"
        }
        submit_resp = requests.post(f"{BASE_URL}/products/scan", headers=headers, files=files, data=data)

    if submit_resp.status_code != 200:
        print(f"Scan submission failed: {submit_resp.status_code} {submit_resp.text}")
        sys.exit(1)

    job_id = submit_resp.json()["job_id"]
    print(f"Scan job queued! Job ID: {job_id}")

    print("\n=== STEP 3: Polling status until AWAITING_QR_EVIDENCE ===")
    max_retries = 30
    paused = False
    qr_data = {}
    for i in range(max_retries):
        time.sleep(3)
        status_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/status", headers=headers)
        status_data = status_resp.json()
        current_status = status_data.get("status")
        progress = status_data.get("progress_percentage")
        msg = status_data.get("current_stage_message")
        print(f"Poll {i+1}: status={current_status}, progress={progress}%, msg='{msg}'")

        if current_status == "AWAITING_QR_EVIDENCE":
            paused = True
            qr_data = status_data
            break
        elif current_status in ["COMPLETED", "FAILED"]:
            break

    if not paused:
        print(f"ERROR: Expected AWAITING_QR_EVIDENCE, but reached status {current_status}")
        sys.exit(1)

    print("\nSUCCESS: Job paused at AWAITING_QR_EVIDENCE!")
    print(f"Detected QR URL: {qr_data.get('detected_qr_url')}")
    print(f"Code to enter:   {qr_data.get('code_to_enter')}")
    assert qr_data.get("detected_qr_url"), "detected_qr_url should be present"

    print("\n=== STEP 4: Calling Skip QR Evidence endpoint ===")
    skip_resp = requests.post(f"{BASE_URL}/products/scan/{job_id}/skip-qr-evidence", headers=headers)
    print(f"Skip response: {skip_resp.status_code} {skip_resp.text}")
    assert skip_resp.status_code == 200, "Skip endpoint should return 200"

    print("\n=== STEP 5: Polling until COMPLETED ===")
    completed = False
    for i in range(max_retries):
        time.sleep(3)
        status_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/status", headers=headers)
        status_data = status_resp.json()
        current_status = status_data.get("status")
        progress = status_data.get("progress_percentage")
        msg = status_data.get("current_stage_message")
        print(f"Poll {i+1}: status={current_status}, progress={progress}%, msg='{msg}'")

        if current_status == "COMPLETED":
            completed = True
            break
        elif current_status == "FAILED":
            print("Job FAILED!")
            sys.exit(1)

    if not completed:
        print("Timed out waiting for completion")
        sys.exit(1)

    print("\n=== STEP 6: Validating Inspection Results ===")
    result_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/result", headers=headers)
    assert result_resp.status_code == 200, "Failed to get scan result"
    res = result_resp.json()

    print(f"Overall Compliance Status: {res.get('status')}")
    print(f"Overall Verdict: {res.get('overall_compliance_verdict')}")
    print(f"Total Rules Checked: {len(res.get('rule_results', []))}")
    print(f"Detected QR URL in result: {res.get('detected_qr_url')}")
    print(f"Code to enter in result:   {res.get('code_to_enter')}")

    # Check Rule 6(1)(a)
    mfg_rule = None
    for r in res.get("rule_results", []):
        if r.get("rule_id") == "RULE_6_1_A":
            mfg_rule = r
            break

    if mfg_rule:
        print(f"\nRule 6(1)(a) Details:")
        print(f"  Status: {mfg_rule.get('status')}")
        print(f"  Severity: {mfg_rule.get('severity')}")
        print(f"  Remarks: {mfg_rule.get('remarks')}")
        print(f"  Extracted Value: {mfg_rule.get('extracted_value')}")

        assert mfg_rule.get("status") == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW, got {mfg_rule.get('status')}"
        assert mfg_rule.get("severity") == "WARNING", f"Expected WARNING, got {mfg_rule.get('severity')}"
        print("  -> PASSED: Rule 6(1)(a) correctly flagged as NEEDS_REVIEW / WARNING!")
    else:
        raise AssertionError("RULE_6_1_A not found in rule_results")

    print("\n ALL E2E SKIPPED VERIFICATION CHECKS PASSED!")

def run_attended_test():
    print("\n" + "="*50)
    print("=== RUNNING ATTENDED FLOW TEST (QR EVIDENCE UPLOAD) ===")
    print("="*50)
    
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "inspector@legalmetro.gov.in", "password": "inspector123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with open("/app/test_samples/imgqr.jpeg", "rb") as f:
        files = [("images", ("imgqr.jpeg", f, "image/jpeg"))]
        data = {
            "product_name": "Masala Chana Dal Attended Test",
            "category": "Packaged Food",
            "reference_scale_mm": 100.0,
            "inspector_notes": "Testing QR code workflow with evidence upload"
        }
        submit_resp = requests.post(f"{BASE_URL}/products/scan", headers=headers, files=files, data=data)

    job_id = submit_resp.json()["job_id"]
    print(f"Scan job queued! Job ID: {job_id}")

    max_retries = 30
    paused = False
    for i in range(max_retries):
        time.sleep(3)
        status_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/status", headers=headers)
        status_data = status_resp.json()
        current_status = status_data.get("status")
        print(f"Poll {i+1}: status={current_status}")
        if current_status == "AWAITING_QR_EVIDENCE":
            paused = True
            break

    assert paused, "Job should reach AWAITING_QR_EVIDENCE"
    print("Job paused at AWAITING_QR_EVIDENCE! Uploading evidence screenshot...")

    with open("/app/test_samples/dummy_portal_screenshot.png", "rb") as sf:
        ev_files = {"qr_screenshot": ("portal_screenshot.png", sf, "image/png")}
        upload_resp = requests.post(
            f"{BASE_URL}/products/scan/{job_id}/qr-evidence",
            headers=headers,
            files=ev_files
        )

    assert upload_resp.status_code == 200, f"Upload evidence failed: {upload_resp.text}"
    print("Evidence uploaded successfully! Polling for completion...")

    completed = False
    for i in range(max_retries):
        time.sleep(3)
        status_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/status", headers=headers)
        status_data = status_resp.json()
        current_status = status_data.get("status")
        print(f"Poll {i+1}: status={current_status}")
        if current_status == "COMPLETED":
            completed = True
            break
        elif current_status == "FAILED":
            print("Job failed!")
            sys.exit(1)

    assert completed, "Job should complete"
    result_resp = requests.get(f"{BASE_URL}/products/scan/{job_id}/result", headers=headers)
    res = result_resp.json()

    print(f"\nAttended Result Verdict: {res.get('overall_compliance_verdict')}")
    print(f"QR Evidence URL: {res.get('qr_evidence_url')}")

    mfg_rule = None
    for r in res.get("rule_results", []):
        if r.get("rule_id") == "RULE_6_1_A":
            mfg_rule = r
            break

    if mfg_rule:
        print(f"Rule 6(1)(a) Status: {mfg_rule.get('status')}")
        print(f"Rule 6(1)(a) Extracted: {mfg_rule.get('extracted_value')}")
        print(f"Rule 6(1)(a) Remarks: {mfg_rule.get('remarks')}")
        assert mfg_rule.get("status") == "PASS", f"Expected PASS, got {mfg_rule.get('status')}"
        print("  -> PASSED: Rule 6(1)(a) resolved successfully as PASS via attended portal evidence!")
    else:
        raise AssertionError("RULE_6_1_A not found in rule_results")

    print("\n ALL ATTENDED VERIFICATION CHECKS PASSED!")

if __name__ == "__main__":
    run_test()
    run_attended_test()
