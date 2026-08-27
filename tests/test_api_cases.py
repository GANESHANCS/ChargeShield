"""
Phase 3 Backend & API Layer Unit & Integration Test Suite.

Verifies:
1. Health endpoint functionality
2. Case listing, pagination, filtering, and sorting
3. Relational case detail retrieval
4. ML win probability prediction endpoint (Phase 2 integration)
5. SHAP model explanation endpoint
6. Error handling (404 for unknown disputes)
7. End-to-End Data -> Backend -> ML -> API integration flow
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# 1. Health Check Test
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ChargeShield"
    assert data["is_synthetic_data"] is True

# 2, 3, 4, 5. Case List, Pagination, Filtering, Sorting Test
def test_list_cases_pagination_filtering():
    # Standard List
    res = client.get("/api/v1/cases?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) == 10
    assert data["total"] > 0
    assert data["page"] == 1
    
    # Filter by Reason Code
    res_reason = client.get("/api/v1/cases?reason=13.1_MERCH_NOT_RECEIVED")
    assert res_reason.status_code == 200
    items_reason = res_reason.json()["items"]
    for item in items_reason:
        assert item["dispute_reason_code"] == "13.1_MERCH_NOT_RECEIVED"
        
    # Sort by Amount Descending
    res_sort = client.get("/api/v1/cases?sort_by=amount_desc&page_size=5")
    assert res_sort.status_code == 200
    items_sort = res_sort.json()["items"]
    amounts = [item["disputed_amount"] for item in items_sort]
    assert amounts == sorted(amounts, reverse=True)

# 6 & 7. Case Detail & 404 Test
def test_get_case_detail():
    # 1. Get known dispute ID from list
    res_list = client.get("/api/v1/cases?page_size=1")
    known_id = res_list.json()["items"][0]["dispute_id"]
    
    # 2. Get Detail
    res_detail = client.get(f"/api/v1/cases/{known_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    
    assert detail["dispute_id"] == known_id
    assert "dispute" in detail
    assert "customer" in detail
    assert "transaction" in detail
    assert "order" in detail
    assert "delivery" in detail
    assert "communications" in detail
    assert "prediction" in detail
    assert detail["priority"] in ["HIGH", "MEDIUM", "LOW"]
    
    # 3. Non-existent case -> 404
    res_404 = client.get("/api/v1/cases/DSP_NONEXISTENT_999")
    assert res_404.status_code == 404

# 8, 9, 10. ML Prediction Endpoint Test
def test_get_case_prediction():
    res_list = client.get("/api/v1/cases?page_size=1")
    known_id = res_list.json()["items"][0]["dispute_id"]
    
    res_pred = client.get(f"/api/v1/cases/{known_id}/prediction")
    assert res_pred.status_code == 200
    pred = res_pred.json()
    
    assert pred["dispute_id"] == known_id
    assert 0.0 <= pred["win_probability"] <= 1.0
    assert pred["recommendation"] in ["CONTEST", "MANUAL_REVIEW", "DO_NOT_CONTEST"]
    assert pred["model_version"] == "chargeshield_ml_v1"
    assert "explanation" in pred

# 11 & 12. SHAP Model Explanation Endpoint Test
def test_get_case_explanation():
    res_list = client.get("/api/v1/cases?page_size=1")
    known_id = res_list.json()["items"][0]["dispute_id"]
    
    res_exp = client.get(f"/api/v1/cases/{known_id}/explanation")
    assert res_exp.status_code == 200
    exp = res_exp.json()
    
    assert exp["dispute_id"] == known_id
    assert exp["model_version"] == "chargeshield_ml_v1"
    assert "top_positive_factors" in exp
    assert "top_negative_factors" in exp

# 13. End-to-End Data -> Backend -> ML -> API Integration Test
def test_e2e_data_backend_ml_api_integration():
    """
    End-to-End integration test confirming data pipeline, backend service,
    trained ML model, and REST API work as a unified system.
    """
    # Request first case summary
    res_list = client.get("/api/v1/cases?page=1&page_size=1")
    assert res_list.status_code == 200
    case_summary = res_list.json()["items"][0]
    dispute_id = case_summary["dispute_id"]
    
    # Request full case detail
    res_detail = client.get(f"/api/v1/cases/{dispute_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    
    # Validate relational link integrity
    assert detail["transaction"]["transaction_id"] == detail["dispute"]["transaction_id"]
    assert detail["order"]["order_id"] == detail["dispute"]["order_id"]
    assert detail["customer"]["customer_id"] == detail["dispute"]["customer_id"]
    assert detail["delivery"]["order_id"] == detail["dispute"]["order_id"]
    
    # Validate prediction integration
    assert detail["prediction"]["win_probability"] == case_summary["win_probability"]
    assert detail["prediction"]["model_version"] == "chargeshield_ml_v1"
