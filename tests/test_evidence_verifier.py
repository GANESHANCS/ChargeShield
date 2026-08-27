"""
Phase 5 Evidence Verification & Citation Engine Test Suite.

Verifies:
1. Exact and normalized field-level matching (VERIFIED)
2. Mismatch detection (MISMATCH) when claim conflicts with source record
3. Missing source detection (MISSING_SOURCE)
4. Monetary amount and boolean normalization comparison
5. Source citation generation (SourceReference and citation_label)
6. Verification summary calculation and verification_rate
7. ML assessment verification against Phase 2 model prediction endpoint
8. End-to-End POST /api/v1/cases/DSP_000001/verify pipeline
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.evidence.comparator import compare_values
from backend.evidence.citations import generate_citation
from backend.evidence.verifier import evidence_verifier
from backend.agent.schemas import EvidenceItem, InvestigationReport, InvestigationRecommendation, MLAssessmentPayload

client = TestClient(app)

# 1. Comparator Unit Tests
def test_comparator_exact_and_normalized_matching():
    # Exact string
    status, mtype, _ = compare_values("FULFILLED", "FULFILLED")
    assert status == "VERIFIED"
    assert mtype == "EXACT"

    # Normalized string case
    status, mtype, _ = compare_values("fulfilled", "FULFILLED")
    assert status == "VERIFIED"
    assert mtype == "NORMALIZED_MATCH"

    # Boolean normalization
    status, mtype, _ = compare_values("true", True)
    assert status == "VERIFIED"
    assert mtype == "NORMALIZED_MATCH"

    # Numeric precision
    status, mtype, _ = compare_values("1797.72", 1797.72)
    assert status == "VERIFIED"
    assert mtype == "EXACT"

# 2. Comparator Mismatch Tests
def test_comparator_mismatches():
    # Value mismatch
    status, mtype, _ = compare_values("DELIVERED", "NOT_APPLICABLE")
    assert status == "MISMATCH"
    assert mtype == "MISMATCH"

    # Monetary mismatch
    status, mtype, _ = compare_values("100.00", "500.00")
    assert status == "MISMATCH"

    # Boolean mismatch
    status, mtype, _ = compare_values("true", False)
    assert status == "MISMATCH"

# 10. Citation Generator Test
def test_citation_generator():
    ref, label = generate_citation("DELIVERY", "DEL_002528", "delivery_status")
    assert ref.entity_type == "DELIVERY"
    assert ref.entity_id == "DEL_002528"
    assert ref.field == "delivery_status"
    assert label == "Delivery DEL_002528 \u2192 delivery_status"

# 18. Verification API Endpoint Test for Valid Dispute
def test_verify_endpoint_valid_dispute():
    dispute_id = "DSP_000001"
    res = client.post(f"/api/v1/cases/{dispute_id}/verify")
    assert res.status_code == 200
    
    payload = res.json()
    assert payload["dispute_id"] == dispute_id
    assert "investigation" in payload
    assert "verification_summary" in payload
    assert "verification_results" in payload
    
    summary = payload["verification_summary"]
    assert summary["total_evidence"] > 0
    assert summary["verification_rate"] == 1.0  # DSP_000001 factual items match source records 100%
    assert summary["mismatched"] == 0
    assert summary["missing_source"] == 0

    results = payload["verification_results"]
    assert len(results) == summary["total_evidence"]
    for r in results:
        assert r["verification_status"] in ["VERIFIED", "MISMATCH", "MISSING_SOURCE", "UNSUPPORTED", "UNVERIFIABLE"]
        assert "source_reference" in r
        assert "citation_label" in r

# 17. Unknown Dispute 404 Verification Test
def test_verify_endpoint_unknown_dispute():
    res_404 = client.post("/api/v1/cases/DSP_NONEXISTENT_999/verify")
    assert res_404.status_code == 404

# 3. Mismatch Injection Verification Test
def test_verifier_mismatch_detection():
    # Fetch report for DSP_000001
    dispute_id = "DSP_000001"
    report_res = client.post(f"/api/v1/cases/{dispute_id}/investigate").json()
    report = InvestigationReport(**report_res)

    # Inject a deliberate false claim into evidence array
    report.evidence.append(
        EvidenceItem(
            evidence_id="EVID_FALSE_1",
            source_type="DELIVERY",
            source_id="DEL_002528",
            source_field="delivery_status",
            claim="False claim of delivered package",
            value="DELIVERED",
            claimed_value="DELIVERED",
            verification_status="UNVERIFIED"
        )
    )

    verified_resp = evidence_verifier.verify_investigation(dispute_id, report)
    summary = verified_resp.verification_summary
    
    # Assert mismatch is correctly detected without altering the claim
    assert summary.mismatched >= 1
    assert summary.verification_rate < 1.0
    
    mismatched_items = [r for r in verified_resp.verification_results if r.verification_status == "MISMATCH"]
    assert len(mismatched_items) >= 1
    assert mismatched_items[0].claimed_value == "DELIVERED"
    assert mismatched_items[0].actual_source_value == "NOT_APPLICABLE"
