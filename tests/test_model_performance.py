"""
Test suite for Model Performance Endpoint GET /api/v1/model/performance.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_model_performance_endpoint():
    res = client.get("/api/v1/model/performance")
    assert res.status_code == 200
    data = res.json()
    assert "model_metadata" in data
    assert "evaluation_report" in data
    
    report = data["evaluation_report"]
    assert "primary_lightgbm_optimal_threshold" in report
    assert report["primary_lightgbm_optimal_threshold"]["threshold"] == 0.29
    assert "financial_cost_simulation_inr" in report
