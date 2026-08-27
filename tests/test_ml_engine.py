"""
Phase 2 ML Engine Unit & Integration Test Suite.

Verifies:
1. Feature generation and pre-triage schema correctness
2. Target and post-outcome field exclusion (leakage gate)
3. Train/validation/test chronological separation
4. Baseline and LightGBM model training
5. Probability output bounds (0.0 to 1.0)
6. Cost-optimal decision threshold selection
7. SHAP explainability feature attribution
8. Model artifact persistence and reloading
"""

import os
import pytest
import numpy as np
import pandas as pd
import joblib

from ml.config import config
from ml.dataset import load_and_split_dataset
from ml.features import construct_features, build_preprocessing_pipeline, ALL_FEATURE_COLUMNS, FORBIDDEN_FIELDS
from ml.train import train_and_optimize
from ml.evaluate import evaluate_models
from ml.predict import ChargebackPredictor

@pytest.fixture
def dataset_data():
    return load_and_split_dataset(data_dir=config.DATA_DIR)

@pytest.fixture
def trained_artifacts():
    return train_and_optimize(data_dir=config.DATA_DIR, output_dir=config.ARTIFACTS_DIR)

# 1 & 2. Feature Generation & Schema Test
def test_feature_generation(dataset_data):
    X_train = dataset_data["X_train"]
    assert len(X_train) > 0
    for col in ALL_FEATURE_COLUMNS:
        assert col in X_train.columns, f"Feature '{col}' missing from X_train!"

# 3 & 4 & 13. Target & Post-Outcome Field Exclusion (Leakage Prevention)
def test_leakage_exclusion(dataset_data):
    X_train = dataset_data["X_train"]
    X_val = dataset_data["X_val"]
    X_test = dataset_data["X_test"]
    
    for df in [X_train, X_val, X_test]:
        for forbidden in FORBIDDEN_FIELDS:
            assert forbidden not in df.columns, f"Leaked field '{forbidden}' found in feature matrix!"

# 5 & 6. Preprocessing Pipeline & Imputation Test
def test_preprocessing_pipeline(dataset_data):
    X_train = dataset_data["X_train"]
    preprocessor = build_preprocessing_pipeline()
    X_proc = preprocessor.fit_transform(X_train)
    
    assert X_proc.shape[0] == len(X_train)
    assert not np.isnan(X_proc).any(), "Preprocessed matrix contains NaN values!"

# 7. Train / Val / Test Separation Test
def test_chronological_split(dataset_data):
    meta_train = dataset_data["meta_train"]
    meta_val = dataset_data["meta_val"]
    meta_test = dataset_data["meta_test"]
    
    train_max_date = pd.to_datetime(meta_train["dispute_creation_timestamp"]).max()
    val_min_date = pd.to_datetime(meta_val["dispute_creation_timestamp"]).min()
    val_max_date = pd.to_datetime(meta_val["dispute_creation_timestamp"]).max()
    test_min_date = pd.to_datetime(meta_test["dispute_creation_timestamp"]).min()
    
    assert train_max_date <= val_min_date, "Chronological train/val overlap detected!"
    assert val_max_date <= test_min_date, "Chronological val/test overlap detected!"

# 8, 9 & 11. Model Training, Probability Output Bounds & Reproducibility
def test_model_training_and_reproducibility(dataset_data):
    res1 = train_and_optimize(data_dir=config.DATA_DIR, output_dir=config.ARTIFACTS_DIR)
    model1 = res1["primary_model"]
    preprocessor = res1["preprocessor"]
    
    X_test = dataset_data["X_test"]
    X_test_proc = preprocessor.transform(X_test)
    probs1 = model1.predict_proba(X_test_proc)[:, 1]
    
    assert (probs1 >= 0.0).all() and (probs1 <= 1.0).all(), "Probabilities outside [0, 1] bounds!"
    
    res2 = train_and_optimize(data_dir=config.DATA_DIR, output_dir=config.ARTIFACTS_DIR)
    probs2 = res2["primary_model"].predict_proba(res2["preprocessor"].transform(X_test))[:, 1]
    
    np.testing.assert_allclose(probs1, probs2, err_msg="Model training is not reproducible across identical seed!")

# 10 & 14 & 15. Predictor API & Artifact Reloading Test
def test_predictor_api_reloading():
    train_and_optimize(data_dir=config.DATA_DIR, output_dir=config.ARTIFACTS_DIR)
    
    predictor = ChargebackPredictor(artifacts_dir=config.ARTIFACTS_DIR)
    pred_res = predictor.predict_dispute_by_id("DSP_000001")
    
    assert "dispute_id" in pred_res
    assert "win_probability" in pred_res
    assert 0.0 <= pred_res["win_probability"] <= 1.0
    assert pred_res["recommendation"] in ["CONTEST", "MANUAL_REVIEW", "DO_NOT_CONTEST"]
    assert "explanation" in pred_res
    assert "top_positive_factors" in pred_res["explanation"]

# 12. Threshold Behavior Test
def test_threshold_selection(trained_artifacts):
    opt_thresh = trained_artifacts["optimal_threshold"]
    assert 0.10 <= opt_thresh <= 0.90
