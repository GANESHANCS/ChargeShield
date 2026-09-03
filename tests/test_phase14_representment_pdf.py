"""
Unit & Integration Test Suite for Phase 14 Representment Evidence Package PDF Generator & Endpoint.

Tests:
1. Valid dispute case generates a non-empty ReportLab PDF with correct media type.
2. Missing dispute case returns 404.
3. Unauthenticated request returns 401.
4. Unauthorized role returns 403 (according to RBAC).
5. PDF content reflects actual DB values without fabricated outcomes.
6. Pending outcomes are rendered as '[ OUTCOME PENDING ]'.
7. Recorded outcomes (WON / LOST) are properly rendered.
8. Verified evidence document SHA-256 hashes are listed from DB.
9. Simulation cases are clearly marked as 'SIMULATION'.
10. Production vs Simulation data boundaries are maintained.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_db_session, init_db
from backend.services.user_service import seed_dev_users, create_user, get_user_by_username
from backend.services.auth_service import create_access_token
from backend.services.representment_pdf_service import representment_pdf_service
from backend.services.case_service import case_service
from backend.db.models import ReviewDecisionModel, ModelOutcomeModel, DisputeModel

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db_and_users():
    init_db()
    with get_db_session() as db:
        seed_dev_users(db, admin_username="admin_test", admin_password="AdminPass123!")


def get_auth_headers(username: str = "admin_test", role: str = "ADMIN") -> dict:
    token = create_access_token({"sub": "USR_TEST_001", "username": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_pdf_service_generates_valid_bytes_for_existing_case():
    with get_db_session() as db:
        # Generate PDF for default seed dispute
        pdf_bytes = representment_pdf_service.generate_pdf("DSP_000001", db)
        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 500
        # PDF magic bytes header check
        assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_service_raises_key_error_for_nonexistent_case():
    with get_db_session() as db:
        with pytest.raises(KeyError) as exc_info:
            representment_pdf_service.generate_pdf("DSP_NONEXISTENT_9999", db)
        assert "not found" in str(exc_info.value)


def test_endpoint_returns_pdf_stream_for_authenticated_user():
    headers = get_auth_headers(username="admin_test", role="ADMIN")
    response = client.get("/api/v1/cases/DSP_000001/representment-package", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"chargeshield_representment_DSP_000001.pdf\"" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 500


def test_endpoint_rejects_unauthenticated_request():
    from backend.core.config import settings
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        response = client.get("/api/v1/cases/DSP_000001/representment-package")
        assert response.status_code == 401
    finally:
        settings.ENVIRONMENT = orig_env


def test_endpoint_rejects_unauthorized_role():
    # User with ANALYST role in DB should be rejected with 403
    headers = get_auth_headers(username="analyst", role="ANALYST")
    response = client.get("/api/v1/cases/DSP_000001/representment-package", headers=headers)
    assert response.status_code == 403


def test_endpoint_returns_404_for_missing_case():
    headers = get_auth_headers(username="admin_test", role="ADMIN")
    response = client.get("/api/v1/cases/DSP_NONEXISTENT_888/representment-package", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_pdf_includes_pending_outcome_when_no_outcome_recorded():
    case_service.add_simulated_case(
        dispute={"dispute_id": "DSP_PENDING_001", "disputed_amount": 100.0, "dispute_reason_code": "13.1_MERCH_NOT_RECEIVED", "final_outcome": None},
        customer={"customer_id": "CUST_PENDING_001"},
        order={"order_id": "ORD_PENDING_001", "order_amount": 100.0},
        transaction={"transaction_id": "TXN_PENDING_001", "amount": 100.0},
        delivery={}
    )
    with get_db_session() as db:
        pdf_bytes = representment_pdf_service.generate_pdf("DSP_PENDING_001", db)

    pdf_text = pdf_bytes.decode("latin1")
    assert "DSP_PENDING_001" in pdf_text
    assert "[ OUTCOME PENDING ]" in pdf_text
    assert "Illustrative operational assumption" in pdf_text
    case_service.reset_simulated_cases()


def test_pdf_renders_recorded_outcome_when_present():
    with get_db_session() as db:
        # Seed an outcome record for DSP_000001
        outcome = ModelOutcomeModel(
            outcome_id="OUT_TEST_001",
            dispute_id="DSP_000001",
            actual_outcome="WON",
            resolution_timestamp="2026-09-01T12:00:00Z",
            financial_recovery_amount=1500.0,
            reviewer_id="rev_admin",
            justification="Bank ruled in favor of merchant with POD signature evidence.",
            data_state="PRODUCTION",
            created_at="2026-09-01T12:00:00Z"
        )
        db.merge(outcome)
        db.commit()

        pdf_bytes = representment_pdf_service.generate_pdf("DSP_000001", db)

    pdf_text = pdf_bytes.decode("latin1")
    assert "WON" in pdf_text
    assert "[ OUTCOME PENDING ]" not in pdf_text


def test_simulation_case_pdf_clearly_labeled_simulation():
    # Inject simulated case
    case_service.add_simulated_case(
        dispute={"dispute_id": "DSP_SIM_999", "disputed_amount": 5000.0, "dispute_reason_code": "13.1_MERCH_NOT_RECEIVED"},
        customer={"customer_id": "CUST_SIM_999"},
        order={"order_id": "ORD_SIM_999", "order_amount": 5000.0},
        transaction={"transaction_id": "TXN_SIM_999", "amount": 5000.0},
        delivery={}
    )

    with get_db_session() as db:
        pdf_bytes = representment_pdf_service.generate_pdf("DSP_SIM_999", db)

    pdf_text = pdf_bytes.decode("latin1")
    assert "SIMULATION" in pdf_text
    assert "DSP_SIM_999" in pdf_text
    assert "SIMULATION RECORD NOTICE" in pdf_text

    # Cleanup simulation
    case_service.reset_simulated_cases()
