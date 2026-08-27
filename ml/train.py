"""
ChargeShield ML Model Training Engine.

Trains Baseline (Logistic Regression) and Primary (LightGBM) models,
performs cost-sensitive decision threshold selection on Validation data,
and persists model artifacts.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
from sklearn.linear_model import LogisticRegression
from lightgbm import LGBMClassifier

from ml.config import config
from ml.features import build_preprocessing_pipeline
from ml.dataset import load_and_split_dataset

def train_and_optimize(
    data_dir: str = config.DATA_DIR,
    output_dir: str = config.ARTIFACTS_DIR
) -> Dict[str, Any]:
    """
    Executes complete ML training pipeline.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load dataset with chronological split
    data = load_and_split_dataset(data_dir=data_dir)
    
    X_train, y_train = data["X_train"], data["y_train"]
    X_val, y_val = data["X_val"], data["y_val"]
    meta_val = data["meta_val"]
    
    # 2. Fit Preprocessing Pipeline ONLY on Training Data (Leakage Gate)
    preprocessor = build_preprocessing_pipeline()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    
    # 3. Baseline Model (Logistic Regression)
    baseline_model = LogisticRegression(**config.LOGISTIC_PARAMS)
    baseline_model.fit(X_train_proc, y_train)
    
    # 4. Primary Model (LightGBM)
    primary_model = LGBMClassifier(**config.LIGHTGBM_PARAMS)
    primary_model.fit(X_train_proc, y_train)
    
    # 5. Cost-Sensitive Threshold Selection on Validation Set
    val_probs = primary_model.predict_proba(X_val_proc)[:, 1]
    best_threshold, min_cost, threshold_results = select_cost_optimal_threshold(
        y_val=y_val,
        val_probs=val_probs,
        disputed_amounts=meta_val["disputed_amount"].values
    )
    
    # 6. Save Model Artifacts
    artifact_payload = {
        "primary_model": primary_model,
        "baseline_model": baseline_model,
        "preprocessor": preprocessor,
        "optimal_threshold": best_threshold,
        "config": {
            "fp_cost_mult": config.FP_COST_MULTIPLIER,
            "fn_cost_mult": config.FN_COST_MULTIPLIER,
            "seed": config.SEED
        }
    }
    
    joblib.dump(artifact_payload, os.path.join(output_dir, "model.joblib"))
    joblib.dump(preprocessor, os.path.join(output_dir, "preprocessor.joblib"))
    
    metadata = {
        "model_name": "ChargeShield ML Win-Probability Engine",
        "model_version": "chargeshield_ml_v1",
        "primary_algorithm": "LightGBM Classifier",
        "baseline_algorithm": "Logistic Regression",
        "random_seed": config.SEED,
        "optimal_cost_threshold": round(float(best_threshold), 4),
        "validation_min_cost_inr": round(float(min_cost), 2),
        "train_samples": data["train_size"],
        "val_samples": data["val_size"],
        "test_samples": data["test_size"]
    }
    
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    return {
        "primary_model": primary_model,
        "baseline_model": baseline_model,
        "preprocessor": preprocessor,
        "optimal_threshold": best_threshold,
        "val_min_cost": min_cost,
        "dataset_info": data,
        "metadata": metadata
    }

def select_cost_optimal_threshold(
    y_val: np.ndarray,
    val_probs: np.ndarray,
    disputed_amounts: np.ndarray
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Finds decision threshold t that minimizes total expected financial cost on Validation Set.
    Cost = FP_cost * FalsePositives + FN_cost * FalseNegatives
    """
    thresholds = np.linspace(0.10, 0.90, 81)
    results = []
    
    best_threshold = config.DEFAULT_THRESHOLD
    min_cost = float("inf")
    
    for t in thresholds:
        preds = (val_probs >= t).astype(int)
        
        # False Positives: predicted contest (1), actual lost (0) -> Wasted filing fee
        fp_mask = (preds == 1) & (y_val == 0)
        # False Negatives: predicted do not contest (0), actual won (1) -> Lost recoverable revenue
        fn_mask = (preds == 0) & (y_val == 1)
        
        fp_cost = np.sum(disputed_amounts[fp_mask] * config.FP_COST_MULTIPLIER)
        fn_cost = np.sum(disputed_amounts[fn_mask] * config.FN_COST_MULTIPLIER)
        total_cost = fp_cost + fn_cost
        
        results.append({
            "threshold": round(float(t), 2),
            "total_cost": round(float(total_cost), 2),
            "fp_count": int(np.sum(fp_mask)),
            "fn_count": int(np.sum(fn_mask))
        })
        
        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = t
            
    return best_threshold, min_cost, results

if __name__ == "__main__":
    train_and_optimize()
    print("Model training and cost-sensitive threshold selection complete.")
