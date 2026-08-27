"""
Pytest test suite for ChargeShield Phase 7 Intelligence Services.
Verifies Financial Engine calculations and Risk Engine scoring & priority reasoning.
"""

import pytest
from backend.services.financial_engine import financial_engine, FinancialEngine, FINANCIAL_ASSUMPTIONS
from backend.services.risk_engine import risk_engine, RiskEngine, RISK_THRESHOLDS

def test_financial_engine_calculations():
    # Test case: Disputed Amount ₹50,000, Win Prob 0.80
    impact = financial_engine.calculate_impact(50000.0, 0.80)
    
    assert impact["disputed_amount"] == 50000.0
    assert impact["currency"] == "INR"
    assert impact["expected_recovery"] == 40000.0  # 50,000 * 0.80
    assert impact["expected_loss"] == 10000.0      # 50,000 * 0.20
    
    # Op Cost: 1,500 + (50,000 * 0.25) = 1,500 + 12,500 = 14,000
    assert impact["estimated_operational_cost"] == 14000.0
    
    # Expected Net Contest Value = 40,000 - 14,000 = 26,000
    assert impact["expected_net_contest_value"] == 26000.0
    
    # Expected Net Accept Value = -50,000
    assert impact["expected_net_accept_value"] == -50000.0
    
    # Net Financial Advantage = 26,000 - (-50,000) = 76,000
    assert impact["net_financial_advantage"] == 76000.0
    assert impact["is_financially_viable"] is True

def test_financial_engine_unviable_dispute():
    # Test case: Low amount ₹1,000, Win Prob 0.20
    # Expected Recovery = 200
    # Op Cost = 1,500 + 250 = 1,750
    # Net Contest Value = 200 - 1,750 = -1,550
    impact = financial_engine.calculate_impact(1000.0, 0.20)
    assert impact["expected_net_contest_value"] == -1550.0
    assert impact["is_financially_viable"] is False

def test_financial_assumptions_transparency():
    impact = financial_engine.calculate_impact(20000.0, 0.50)
    assert "assumptions" in impact
    assert impact["assumptions"]["base_filing_fee"] == 1500.0
    assert impact["assumptions"]["contest_fee_multiplier"] == 0.25
    assert "disclaimer" in impact["assumptions"]

def test_risk_engine_critical_assessment():
    res = risk_engine.assess_risk(
        dispute_id="DSP_000001",
        transaction_id="TXN_000001",
        amount=60000.0,
        dispute_reason="13.1_MERCH_NOT_RECEIVED",
        win_probability=0.85
    )
    
    assert res["dispute_id"] == "DSP_000001"
    assert res["priority"] == "CRITICAL"
    assert res["recommended_action"] == "CONTEST"
    assert res["confidence"] > 0.80
    assert "CRITICAL" in res["priority_reasoning"]
    assert "₹60,000 at stake" in res["priority_reasoning"]

def test_risk_engine_high_risk_low_win_prob():
    res = risk_engine.assess_risk(
        dispute_id="DSP_000002",
        transaction_id="TXN_000002",
        amount=15000.0,
        dispute_reason="10.4_OTHER",
        win_probability=0.10
    )
    
    assert res["priority"] == "HIGH"
    assert res["recommended_action"] == "DO_NOT_CONTEST"
    assert res["risk_score"] == 0.90

def test_data_quality_service():
    from backend.services.data_quality_service import data_quality_service
    res = data_quality_service.evaluate_quality()
    assert "data_quality_score" in res
    assert res["data_quality_score"] > 80.0
    assert res["status"] in ["EXCELLENT", "GOOD", "DEGRADED"]

def test_explanation_service():
    from backend.services.explanation_service import explanation_service
    exp = explanation_service.generate_explanation(
        dispute_id="DSP_000001",
        dispute_amount=48200.0,
        win_probability=0.87,
        recommendation="CONTEST",
        risk_tier="CRITICAL",
        verification_rate=1.0
    )
    assert "executive_explanation" in exp
    assert "technical_shap" in exp
    assert "DSP_000001" in exp["executive_explanation"]
    assert "CONTEST" in exp["executive_explanation"]

def test_simulation_service():
    from backend.services.simulation_service import simulation_service
    sim = simulation_service.simulate_decision_scenarios(
        dispute_id="DSP_000001",
        disputed_amount=48200.0,
        win_probability=0.87
    )
    assert sim["dispute_id"] == "DSP_000001"
    assert "scenarios" in sim
    assert "CONTEST" in sim["scenarios"]
    assert "DO_NOT_CONTEST" in sim["scenarios"]
    assert "ESCALATE" in sim["scenarios"]
    assert sim["scenarios"]["CONTEST"]["type"] == "MODEL_ESTIMATE"

