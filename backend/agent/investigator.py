"""
Orchestration Agent for Phase 4 Read-Only AI Risk Investigation.
Retrievable via backend service, orchestrates data gathering, ML signal extraction,
and factual report synthesis.
"""

from typing import Dict, Any, Optional
from backend.services.case_service import case_service
from backend.agent.llm import get_llm_provider
from backend.agent.schemas import InvestigationReport
from backend.core.logging import logger

class RiskInvestigationAgent:
    """Read-only AI Risk Investigation Agent for ChargeShield."""
    def __init__(self):
        self.llm_provider = get_llm_provider()

    def investigate_case(self, dispute_id: str) -> InvestigationReport:
        """
        Executes read-only investigation flow for a given dispute_id.
        Retrieves case detail, predictions, and SHAP factors using Phase 3 services.
        Synthesizes factual InvestigationReport.
        """
        logger.info(f"Starting read-only risk investigation for dispute {dispute_id}...")
        
        # 1. Retrieve full relational case details from Phase 3 service
        case_detail = case_service.get_case_detail(dispute_id)
        if not case_detail:
            raise ValueError(f"Dispute case '{dispute_id}' not found.")

        # 2. Synthesize InvestigationReport using LLM Provider or Deterministic Fallback Engine
        report = self.llm_provider.generate_report(case_detail)
        logger.info(f"Investigation completed for {dispute_id}. Action: {report.recommendation.action}, Win Prob: {report.recommendation.win_probability * 100:.1f}%.")
        
        return report

investigation_agent = RiskInvestigationAgent()
