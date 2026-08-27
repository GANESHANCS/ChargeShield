"""
Pydantic API Schemas for ML Prediction & Explainability endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FactorDescription(BaseModel):
    feature_name: str
    shap_value: float
    impact: str = Field(description="POSITIVE or NEGATIVE")
    description: str

class ExplanationPayload(BaseModel):
    top_positive_factors: List[FactorDescription]
    top_negative_factors: List[FactorDescription]
    all_significant_factors: List[FactorDescription]

class PredictionResponse(BaseModel):
    dispute_id: str
    win_probability: float = Field(ge=0.0, le=1.0)
    win_probability_percent: str
    predicted_class: int = Field(description="1 for winnable, 0 for risky/uncontestable")
    recommendation: str = Field(description="CONTEST, MANUAL_REVIEW, or DO_NOT_CONTEST")
    decision_threshold: float
    model_version: str
    prediction_timestamp: str
    explanation: ExplanationPayload
    disclaimer: str

class ExplanationResponse(BaseModel):
    dispute_id: str
    model_version: str
    top_positive_factors: List[FactorDescription]
    top_negative_factors: List[FactorDescription]
    all_significant_factors: List[FactorDescription]
