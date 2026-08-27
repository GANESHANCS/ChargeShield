"""
ChargeShield ML Engine Configuration.
Defines model parameters, dataset split ratios, cost-sensitive matrices, and artifact paths.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MLConfig:
    # Reproducibility
    SEED: int = 42
    
    # Dataset splitting (Time-aware)
    TRAIN_RATIO: float = 0.60
    VAL_RATIO: float = 0.20
    TEST_RATIO: float = 0.20
    
    # Cost-Sensitive Decision Matrix
    # FP Cost: Expense of contesting a lost dispute (dispute filing fee ~ 25% of amount)
    # FN Cost: Lost opportunity of failing to contest a winnable dispute (100% of amount)
    FP_COST_MULTIPLIER: float = 0.25
    FN_COST_MULTIPLIER: float = 1.00
    
    # Default Fallback Threshold
    DEFAULT_THRESHOLD: float = 0.50
    
    # Directories & Artifact Paths
    ARTIFACTS_DIR: str = "ml/artifacts"
    REPORTS_DIR: str = "ml/reports"
    DATA_DIR: str = "data/generated"
    
    MODEL_PATH: str = "ml/artifacts/model.joblib"
    PREPROCESSOR_PATH: str = "ml/artifacts/preprocessor.joblib"
    METADATA_PATH: str = "ml/artifacts/metadata.json"
    
    # Model Hyperparameters
    LIGHTGBM_PARAMS: Dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 100,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "max_depth": 4,
        "class_weight": "balanced",
        "random_state": 42,
        "verbose": -1
    })
    
    LOGISTIC_PARAMS: Dict[str, Any] = field(default_factory=lambda: {
        "class_weight": "balanced",
        "max_iter": 1000,
        "random_state": 42
    })

config = MLConfig()
