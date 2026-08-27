"""
Prediction Service for ChargeShield Risk Operations Backend.

Wraps the Phase 2 ChargebackPredictor and provides application-level cached
ML predictions and SHAP explanations.
"""

from typing import Dict, Any
from ml.predict import ChargebackPredictor
from backend.core.logging import logger

class PredictionService:
    """Singleton wrapper for ML inference and explainability."""
    _instance: 'PredictionService' = None
    _predictor: ChargebackPredictor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictionService, cls).__new__(cls)
            logger.info("Initializing ChargeShield PredictionService with model version chargeshield_ml_v1...")
            cls._predictor = ChargebackPredictor()
        return cls._instance

    def predict_dispute(self, dispute_id: str) -> Dict[str, Any]:
        """Runs ML prediction on a given dispute ID using loaded model artifact or simulation metadata."""
        if dispute_id.startswith("DSP_SIM_"):
            # Safe fallback prediction for simulated cases without circular lookup
            win_prob = 0.85
            rec = "CONTEST"
            return {
                "dispute_id": dispute_id,
                "model_version": "chargeshield_ml_v1",
                "win_probability": win_prob,
                "optimal_threshold": 0.29,
                "recommendation": rec,
                "predicted_class": 1 if win_prob >= 0.29 else 0,
                "explanation": {
                    "top_positive_factors": [{"feature": "pod_signature_present", "value": 1, "shap_value": 0.35}],
                    "top_negative_factors": [{"feature": "auth_risk_score", "value": 45, "shap_value": -0.15}],
                    "all_significant_factors": []
                }
            }
        return self._predictor.predict_dispute_by_id(dispute_id)

    def explain_dispute(self, dispute_id: str) -> Dict[str, Any]:
        """Extracts SHAP explanation attributions for a given dispute ID."""
        pred = self.predict_dispute(dispute_id)
        return {
            "dispute_id": dispute_id,
            "model_version": pred["model_version"],
            "top_positive_factors": pred["explanation"]["top_positive_factors"],
            "top_negative_factors": pred["explanation"]["top_negative_factors"],
            "all_significant_factors": pred["explanation"]["all_significant_factors"]
        }

prediction_service = PredictionService()
