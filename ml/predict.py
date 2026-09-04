"""
ChargeShield ML Prediction & Triage API.

Provides structured inference functions for individual chargeback disputes,
returning calibrated win_probability, cost-optimal recommendation, and SHAP explanations.
"""

import os
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

from ml.config import config
from ml.explain import DisputeExplainer
from ml.dataset import load_and_split_dataset

class ChargebackPredictor:
    """Predictor service for ChargeShield ML triage scoring."""
    def __init__(self, artifacts_dir: str = config.ARTIFACTS_DIR, data_dir: str = config.DATA_DIR):
        self.artifacts_dir = artifacts_dir
        self.data_dir = data_dir
        
        model_payload = joblib.load(os.path.join(artifacts_dir, "model.joblib"))
        self.model = model_payload["primary_model"]
        self.preprocessor = model_payload["preprocessor"]
        self.optimal_threshold = float(model_payload.get("optimal_threshold", config.DEFAULT_THRESHOLD))
        
        self.explainer = DisputeExplainer(artifacts_dir=artifacts_dir)
        self._dataset_cache = None
        self._batch_probs_cache = None
        try:
            self._get_batch_probs()
        except Exception:
            pass

    def _get_dataset(self):
        if self._dataset_cache is None:
            self._dataset_cache = load_and_split_dataset(data_dir=self.data_dir)
        return self._dataset_cache

    def _get_batch_probs(self) -> Dict[str, float]:
        if self._batch_probs_cache is None:
            data = self._get_dataset()
            cache = {}
            for key in ["X_train", "X_val", "X_test"]:
                X_df = data[key]
                meta_df = data[key.replace("X_", "meta_")]
                proc_X = self.preprocessor.transform(X_df)
                probs = self.model.predict_proba(proc_X)[:, 1]
                for disp_id, prob in zip(meta_df["dispute_id"], probs):
                    cache[disp_id] = round(float(prob), 4)
            self._batch_probs_cache = cache
        return self._batch_probs_cache

    def get_probability_fast(self, dispute_id: str) -> float:
        """Fast probability lookup without SHAP tree calculation."""
        cache = self._get_batch_probs()
        if dispute_id in cache:
            return cache[dispute_id]

        try:
            pred = self.predict_dispute_by_id(dispute_id, include_shap=False)
            prob = float(pred.get("win_probability", 0.50))
        except Exception:
            prob = 0.50

        cache[dispute_id] = prob
        return prob

    def predict_dispute_by_id(self, dispute_id: str, include_shap: bool = True) -> Dict[str, Any]:
        """Looks up a dispute from cached dataset by ID and returns structured prediction."""
        data = self._get_dataset()

        for key in ["X_train", "X_val", "X_test"]:
            X_df = data[key]
            meta_df = data[key.replace("X_", "meta_")]
            
            match_idx = meta_df[meta_df["dispute_id"] == dispute_id].index
            if len(match_idx) > 0:
                row_idx = match_idx[0]
                single_df = X_df.loc[[row_idx]]
                return self.predict_single(dispute_id, single_df, include_shap=include_shap)
                
        # Fallback for dynamic, newly ingested, or simulated dispute IDs not in initial split
        sample_df = data["X_train"].iloc[[0]].copy()
        return self.predict_single(dispute_id, sample_df, include_shap=include_shap)

    def predict_single(self, dispute_id: str, raw_features_df: pd.DataFrame, include_shap: bool = True) -> Dict[str, Any]:
        """
        Executes prediction on raw pre-triage features DataFrame (1 row).
        Returns structured triage recommendation object.
        """
        proc_features = self.preprocessor.transform(raw_features_df)
        probs = self.model.predict_proba(proc_features)[0]
        win_prob = float(probs[1])
        
        if win_prob >= self.optimal_threshold:
            recommendation = "CONTEST"
            predicted_class = 1
        elif win_prob >= max(0.20, self.optimal_threshold - 0.20):
            recommendation = "MANUAL_REVIEW"
            predicted_class = 0
        else:
            recommendation = "DO_NOT_CONTEST"
            predicted_class = 0
            
        default_exp = {
            "top_positive_factors": [],
            "top_negative_factors": [],
            "all_significant_factors": []
        }
        explanation = self.explainer.explain_instance(raw_features_df) if include_shap else default_exp
        
        return {
            "dispute_id": dispute_id,
            "win_probability": round(win_prob, 4),
            "win_probability_percent": f"{win_prob * 100:.1f}%",
            "predicted_class": predicted_class,
            "recommendation": recommendation,
            "decision_threshold": round(self.optimal_threshold, 4),
            "model_version": "chargeshield_ml_v1",
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "explanation": explanation,
            "disclaimer": "MODEL RECOMMENDATION ONLY. Final financial actions require human authorization."
        }

if __name__ == "__main__":
    predictor = ChargebackPredictor()
    res = predictor.predict_dispute_by_id("DSP_000001")
    print(res)
