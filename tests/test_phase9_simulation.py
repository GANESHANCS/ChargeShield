"""
Phase 9 Unit and Integration Test Suite for Real-Time Event Intelligence & Simulation.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.simulation_engine import simulation_engine, SCENARIO_PROFILES
from backend.services.event_service import event_service
from backend.services.case_service import case_service

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def reset_case_service_after_module():
    yield
    case_service.reset_simulated_cases()

def test_simulation_start():
    status = simulation_engine.start_simulation("HIGH_RISK_CHARGEBACK")
    assert status["running"] is True
    assert status["scenario"] == "HIGH_RISK_CHARGEBACK"
    assert status["data_state"] == "SIMULATION"

def test_simulation_stop():
    status = simulation_engine.stop_simulation()
    assert status["running"] is False

def test_simulation_status():
    status = simulation_engine.get_status()
    assert "running" in status
    assert "events_processed" in status
    assert "transactions_processed" in status
    assert status["data_state"] == "SIMULATION"

def test_scenario_validation():
    status = simulation_engine.start_simulation("INVALID_SCENARIO_XYZ")
    assert status["scenario"] == "NORMAL_TRANSACTION"

def test_deterministic_scenario_generation():
    res = simulation_engine.generate_transaction("CRITICAL_VALUE_DISPUTE")
    assert res["scenario"] == "CRITICAL_VALUE_DISPUTE"
    assert res["disputed_amount"] == 75000.0
    assert res["priority"] == "CRITICAL"
    assert res["data_state"] == "SIMULATION"

def test_transaction_creation():
    res = simulation_engine.generate_transaction("NORMAL_TRANSACTION")
    assert res["dispute_id"].startswith("DSP_SIM_")
    assert res["transaction_id"].startswith("TXN_SIM_")

def test_event_generation():
    initial_events = len(event_service.get_events(limit=500))
    simulation_engine.generate_transaction("NORMAL_TRANSACTION")
    new_events = event_service.get_events(limit=500)
    assert len(new_events) >= initial_events + 8

def test_event_ordering():
    events = event_service.get_events(limit=10)
    assert len(events) > 0
    event_types = [e["event_type"] for e in events]
    assert "TRANSACTION_RECEIVED" in event_types or "CASE_CREATED" in event_types

def test_data_state_labeling():
    events = event_service.get_events(limit=10)
    for ev in events:
        assert ev["data_state"] in ["SIMULATION", "HISTORICAL", "PRODUCTION"]

def test_intelligence_pipeline_integration():
    res = simulation_engine.generate_transaction("HIGH_WIN_PROBABILITY_CASE")
    assert res["win_probability"] == 0.94
    assert res["recommendation"] == "CONTEST"

def test_case_creation():
    res = simulation_engine.generate_transaction("EVIDENCE_MISMATCH")
    disp_id = res["dispute_id"]
    case_detail = case_service.get_case_detail(disp_id)
    assert case_detail is not None
    assert case_detail["dispute"]["dispute_id"] == disp_id

def test_queue_visibility():
    res = simulation_engine.generate_transaction("REPEAT_DISPUTE_CUSTOMER")
    disp_id = res["dispute_id"]
    cases_resp = case_service.list_cases(page=1, page_size=100, data_state="SIMULATION")
    disp_ids = [c["dispute_id"] for c in cases_resp["items"]]
    assert disp_id in disp_ids

def test_simulation_isolation():
    events = event_service.get_events(data_state="SIMULATION", limit=50)
    for e in events:
        assert e["data_state"] == "SIMULATION"

def test_simulation_api_endpoints():
    response = client.post("/api/v1/simulation/start", json={"scenario": "NORMAL_TRANSACTION"})
    assert response.status_code == 200
    assert response.json()["running"] is True

    txn_resp = client.post("/api/v1/simulation/transaction")
    assert txn_resp.status_code == 200
    assert "dispute_id" in txn_resp.json()

    events_resp = client.get("/api/v1/simulation/events")
    assert events_resp.status_code == 200
    assert isinstance(events_resp.json(), list)

    scenarios_resp = client.get("/api/v1/simulation/scenarios")
    assert scenarios_resp.status_code == 200
    assert len(scenarios_resp.json()) == 8

    stop_resp = client.post("/api/v1/simulation/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["running"] is False

def test_simulation_error_handling():
    resp = client.get("/api/v1/simulation/events?limit=9999")
    assert resp.status_code == 422  # Validation error (>500 limit)

def test_multiple_simulation_transactions():
    for _ in range(3):
        res = simulation_engine.generate_transaction("LOW_RISK_CHARGEBACK")
        assert res["data_state"] == "SIMULATION"

def test_simulation_restart_behavior():
    client.post("/api/v1/simulation/start", json={"scenario": "HIGH_RISK_CHARGEBACK"})
    client.post("/api/v1/simulation/stop")
    status = client.get("/api/v1/simulation/status").json()
    assert status["running"] is False
