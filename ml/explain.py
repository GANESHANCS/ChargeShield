"""
ChargeShield SHAP Explainability Engine.

Extracts per-prediction SHAP attributions for tree-based primary models,
mapping raw feature importances to human-readable risk factors.
"""

import os
import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from ml.config import config

class DisputeExplainer:
    """SHAP explainer for ChargeShield predictions."""
    def __init__(self, artifacts_dir: str = config.ARTIFACTS_DIR):
        model_payload = joblib.load(os.path.join(artifacts_dir, "model.joblib"))
        self.model = model_payload["primary_model"]
        self.preprocessor = model_payload["preprocessor"]
        
        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)
        
        # Feature names after preprocessing
        try:
            self.feature_names = self.preprocessor.get_feature_names_out()
        except AttributeError:
            self.feature_names = [f"feature_{i}" for i in range(100)]

    def explain_instance(self, raw_features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates SHAP values for a single row DataFrame of pre-triage features.
        Returns top positive and negative contributing factors.
        """
        proc_features = self.preprocessor.transform(raw_features_df)
        shap_vals = self.explainer.shap_values(proc_features)
        
        # Binary classification SHAP values array handling
        if isinstance(shap_vals, list):
            sv = shap_vals[1][0] # class 1 (win) SHAP values
        elif len(shap_vals.shape) == 3:
            sv = shap_vals[0, :, 1]
        elif len(shap_vals.shape) == 2:
            sv = shap_vals[0]
        else:
            sv = shap_vals
            
        top_factors = []
        for idx in range(len(sv)):
            val = float(sv[idx])
            if abs(val) > 0.01:
                name = self.feature_names[idx]
                top_factors.append({
                    "feature_name": name,
                    "shap_value": round(val, 4),
                    "impact": "POSITIVE" if val > 0 else "NEGATIVE",
                    "description": self._format_feature_description(name, val)
                })
                
        # Sort by absolute SHAP magnitude
        top_factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        pos_factors = [f for f in top_factors if f["impact"] == "POSITIVE"][:4]
        neg_factors = [f for f in top_factors if f["impact"] == "NEGATIVE"][:4]
        
        return {
            "top_positive_factors": pos_factors,
            "top_negative_factors": neg_factors,
            "all_significant_factors": top_factors[:10]
        }

    def generate_summary_plot(self, X_sample: pd.DataFrame, reports_dir: str = config.REPORTS_DIR):
        """Generates global SHAP summary plot for dataset sample."""
        try:
            proc_X = self.preprocessor.transform(X_sample)
            shap_values = self.explainer.shap_values(proc_X)
            
            if isinstance(shap_values, list):
                sv = shap_values[1]
            else:
                sv = shap_values
                
            plt.figure(figsize=(8, 6))
            shap.summary_plot(sv, proc_X, feature_names=self.feature_names, show=False)
            plt.tight_layout()
            plt.savefig(os.path.join(reports_dir, "shap_summary.png"), dpi=150)
            plt.close()
        except Exception as e:
            print(f"SHAP summary plot generation skipped: {e}")

    def _format_feature_description(self, feature_name: str, shap_val: str) -> str:
        clean_name = feature_name.split("__")[-1]
        
        descriptions = {
            "pod_signature_present": "Proof of Delivery (POD) signature verified on carrier tracking",
            "device_fingerprint_match": "Transaction device fingerprint matches customer historical baseline",
            "ip_country_match": "IP address country matches customer billing country",
            "customer_contacted_support": "Customer support interaction recorded prior to dispute filing",
            "support_ticket_resolved": "Merchant support ticket was marked resolved before chargeback",
            "delivery_status_DELIVERED": "Carrier logistics tracking confirms completed package delivery",
            "delivery_status_FAILED": "Package delivery failed or carrier returned item to merchant",
            "previous_chargeback_count": "Customer has historical chargebacks lost by merchant",
            "customer_success_ratio": "Customer historical order completion and non-dispute ratio",
            "auth_risk_score": "Payment gateway authorization risk assessment score"
        }
        
        return descriptions.get(clean_name, f"Feature '{clean_name}' influenced win probability by {shap_val:+.2f}")
