"""
Financial Impact Engine for ChargeShield Phase 7.

Calculates explicit monetary impact, operational contest costs, expected recovery,
and net financial advantage for chargeback dispute management.
Uses explicit, configurable deployment assumptions.
"""

from typing import Dict, Any, Optional

# Configurable deployment assumptions (not universal real-world facts)
FINANCIAL_ASSUMPTIONS: Dict[str, Any] = {
    "base_filing_fee": 1500.0,
    "contest_fee_multiplier": 0.25,
    "currency": "INR",
    "disclaimer": "Illustrative operational deployment assumptions. Base filing fee = ₹1,500; Contest fee multiplier = 25% of dispute amount."
}

class FinancialEngine:
    """Calculates explicit monetary metrics for individual chargeback disputes."""

    def __init__(self, assumptions: Optional[Dict[str, Any]] = None):
        self.assumptions = assumptions or FINANCIAL_ASSUMPTIONS

    def calculate_impact(self, disputed_amount: float, win_probability: float) -> Dict[str, Any]:
        """
        Calculates expected financial outcome for contesting vs accepting a dispute.
        
        Formulas:
          - Expected Recovery = Disputed Amount * Win Probability
          - Expected Loss = Disputed Amount * (1 - Win Probability)
          - Estimated Operational Cost = Base Filing Fee + (Disputed Amount * Contest Fee Multiplier)
          - Expected Net Contest Value = Expected Recovery - Estimated Operational Cost
          - Expected Net Accept Value = -1 * Disputed Amount
          - Net Financial Advantage = Expected Net Contest Value - Expected Net Accept Value
        """
        amount = max(0.0, float(disputed_amount))
        win_prob = max(0.0, min(1.0, float(win_probability)))

        base_fee = float(self.assumptions.get("base_filing_fee", 1500.0))
        multiplier = float(self.assumptions.get("contest_fee_multiplier", 0.25))

        expected_recovery = round(amount * win_prob, 2)
        expected_loss = round(amount * (1.0 - win_prob), 2)
        potential_recovery = round(amount, 2)

        estimated_op_cost = round(base_fee + (amount * multiplier), 2)
        expected_net_contest_value = round(expected_recovery - estimated_op_cost, 2)
        expected_net_accept_value = round(-1.0 * amount, 2)

        net_financial_advantage = round(expected_net_contest_value - expected_net_accept_value, 2)

        is_financially_viable = expected_net_contest_value > expected_net_accept_value and expected_net_contest_value > 0

        return {
            "disputed_amount": amount,
            "currency": self.assumptions.get("currency", "INR"),
            "expected_recovery": expected_recovery,
            "expected_loss": expected_loss,
            "potential_recovery_value": potential_recovery,
            "estimated_operational_cost": estimated_op_cost,
            "expected_net_contest_value": expected_net_contest_value,
            "expected_net_accept_value": expected_net_accept_value,
            "net_financial_advantage": net_financial_advantage,
            "is_financially_viable": is_financially_viable,
            "assumptions": {
                "base_filing_fee": base_fee,
                "contest_fee_multiplier": multiplier,
                "currency": self.assumptions.get("currency", "INR"),
                "disclaimer": self.assumptions.get("disclaimer", "Illustrative operational deployment assumptions.")
            }
        }

financial_engine = FinancialEngine()
