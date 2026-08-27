"""
ChargeShield Model Evaluation & Reporting Engine.

Evaluates trained baseline and LightGBM models on the untouched Test Set.
Computes Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Brier score, Confusion Matrix,
and generates diagnostic plots.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Headless rendering
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, brier_score_loss,
    confusion_matrix, roc_curve
)
from sklearn.calibration import calibration_curve

from ml.config import config
from ml.dataset import load_and_split_dataset

def evaluate_models(
    data_dir: str = config.DATA_DIR,
    artifacts_dir: str = config.ARTIFACTS_DIR,
    reports_dir: str = config.REPORTS_DIR
) -> Dict[str, Any]:
    """
    Evaluates baseline and primary models on held-out Test Set.
    Generates evaluation report and diagnostic plots.
    """
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. Load artifacts
    model_payload = joblib.load(os.path.join(artifacts_dir, "model.joblib"))
    primary_model = model_payload["primary_model"]
    baseline_model = model_payload["baseline_model"]
    preprocessor = model_payload["preprocessor"]
    optimal_threshold = model_payload["optimal_threshold"]
    
    # 2. Load dataset
    data = load_and_split_dataset(data_dir=data_dir)
    X_test, y_test = data["X_test"], data["y_test"]
    meta_test = data["meta_test"]
    
    # Preprocess test features using training-fitted preprocessor
    X_test_proc = preprocessor.transform(X_test)
    
    # 3. Model Predictions & Probabilities
    base_probs = baseline_model.predict_proba(X_test_proc)[:, 1]
    base_preds = (base_probs >= 0.50).astype(int)
    
    prim_probs = primary_model.predict_proba(X_test_proc)[:, 1]
    prim_preds_default = (prim_probs >= 0.50).astype(int)
    prim_preds_opt = (prim_probs >= optimal_threshold).astype(int)
    
    # 4. Metric Computations
    baseline_metrics = _compute_metrics(y_test, base_preds, base_probs)
    primary_default_metrics = _compute_metrics(y_test, prim_preds_default, prim_probs)
    primary_opt_metrics = _compute_metrics(y_test, prim_preds_opt, prim_probs)
    
    # Financial Cost Simulation on Test Set
    disputed_amounts = meta_test["disputed_amount"].values
    cost_always_contest = _calculate_financial_cost(y_test, np.ones_like(y_test), disputed_amounts)
    cost_default_thresh = _calculate_financial_cost(y_test, prim_preds_default, disputed_amounts)
    cost_optimal_thresh = _calculate_financial_cost(y_test, prim_preds_opt, disputed_amounts)
    
    financial_savings = cost_always_contest - cost_optimal_thresh
    
    evaluation_report = {
        "dataset_summary": {
            "test_disputes": len(y_test),
            "test_won_count": int(np.sum(y_test == 1)),
            "test_lost_count": int(np.sum(y_test == 0)),
            "test_win_rate_percent": round(float(np.mean(y_test == 1) * 100), 2)
        },
        "baseline_logistic_regression": baseline_metrics,
        "primary_lightgbm_default_0.50": primary_default_metrics,
        "primary_lightgbm_optimal_threshold": {
            "threshold": round(float(optimal_threshold), 4),
            "metrics": primary_opt_metrics
        },
        "financial_cost_simulation_inr": {
            "cost_naive_always_contest": round(float(cost_always_contest), 2),
            "cost_model_default_0.50": round(float(cost_default_thresh), 2),
            "cost_model_optimal_threshold": round(float(cost_optimal_thresh), 2),
            "cost_savings_inr": round(float(financial_savings), 2)
        }
    }
    
    # Save Report JSON
    with open(os.path.join(reports_dir, "evaluation_report.json"), "w") as f:
        json.dump(evaluation_report, f, indent=2)
        
    # 5. Generate Diagnostic Plots
    _plot_roc_curve(y_test, base_probs, prim_probs, reports_dir)
    _plot_pr_curve(y_test, base_probs, prim_probs, reports_dir)
    _plot_calibration_curve(y_test, base_probs, prim_probs, reports_dir)
    _plot_confusion_matrix(y_test, prim_preds_opt, reports_dir)
    _plot_feature_importance(primary_model, preprocessor, reports_dir)
    
    return evaluation_report

def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    precision_pr, recall_pr, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_val = auc(recall_pr, precision_pr)
    
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
        "pr_auc": round(float(pr_auc_val), 4),
        "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4)
    }

def _calculate_financial_cost(y_true: np.ndarray, y_pred: np.ndarray, amounts: np.ndarray) -> float:
    fp_mask = (y_pred == 1) & (y_true == 0)
    fn_mask = (y_pred == 0) & (y_true == 1)
    
    fp_cost = np.sum(amounts[fp_mask] * config.FP_COST_MULTIPLIER)
    fn_cost = np.sum(amounts[fn_mask] * config.FN_COST_MULTIPLIER)
    return fp_cost + fn_cost

# Plotting Utilities
def _plot_roc_curve(y_true, base_probs, prim_probs, reports_dir):
    plt.figure(figsize=(6, 5))
    fpr_b, tpr_b, _ = roc_curve(y_true, base_probs)
    fpr_p, tpr_p, _ = roc_curve(y_true, prim_probs)
    
    plt.plot(fpr_b, tpr_b, label=f'Baseline Logistic (AUC = {roc_auc_score(y_true, base_probs):.3f})', linestyle='--')
    plt.plot(fpr_p, tpr_p, label=f'LightGBM Primary (AUC = {roc_auc_score(y_true, prim_probs):.3f})', color='#0066ff', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k:', alpha=0.5)
    
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve Comparison')
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(reports_dir, "roc_curve.png"), dpi=150)
    plt.close()

def _plot_pr_curve(y_true, base_probs, prim_probs, reports_dir):
    plt.figure(figsize=(6, 5))
    p_b, r_b, _ = precision_recall_curve(y_true, base_probs)
    p_p, r_p, _ = precision_recall_curve(y_true, prim_probs)
    
    plt.plot(r_b, p_b, label=f'Baseline Logistic (PR-AUC = {auc(r_b, p_b):.3f})', linestyle='--')
    plt.plot(r_p, p_p, label=f'LightGBM Primary (PR-AUC = {auc(r_p, p_p):.3f})', color='#0066ff', linewidth=2)
    
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve Comparison')
    plt.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig(os.path.join(reports_dir, "pr_curve.png"), dpi=150)
    plt.close()

def _plot_calibration_curve(y_true, base_probs, prim_probs, reports_dir):
    plt.figure(figsize=(6, 5))
    prob_true_b, prob_pred_b = calibration_curve(y_true, base_probs, n_bins=5)
    prob_true_p, prob_pred_p = calibration_curve(y_true, prim_probs, n_bins=5)
    
    plt.plot(prob_pred_b, prob_true_b, 's--', label='Baseline Logistic')
    plt.plot(prob_pred_p, prob_true_p, 'o-', label='LightGBM Primary', color='#0066ff', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k:', label='Perfectly Calibrated')
    
    plt.xlabel('Mean Predicted Probability')
    plt.ylabel('Fraction of Positives (Actual Win Rate)')
    plt.title('Reliability Diagram (Calibration Curve)')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(reports_dir, "calibration_curve.png"), dpi=150)
    plt.close()

def _plot_confusion_matrix(y_true, y_pred, reports_dir):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(5, 4))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Test Set Confusion Matrix')
    plt.colorbar()
    
    tick_marks = [0, 1]
    plt.xticks(tick_marks, ['Lost (0)', 'Won (1)'])
    plt.yticks(tick_marks, ['Lost (0)', 'Won (1)'])
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
                     
    plt.ylabel('True Outcome')
    plt.xlabel('Predicted Decision')
    plt.tight_layout()
    plt.savefig(os.path.join(reports_dir, "confusion_matrix.png"), dpi=150)
    plt.close()

def _plot_feature_importance(model, preprocessor, reports_dir):
    try:
        feature_names = preprocessor.get_feature_names_out()
        importances = model.feature_importances_
        
        idx = np.argsort(importances)[-15:]
        
        plt.figure(figsize=(8, 6))
        plt.barh(range(len(idx)), importances[idx], align='center', color='#0066ff')
        plt.yticks(range(len(idx)), [feature_names[i] for i in idx])
        plt.xlabel('LightGBM Feature Importance (Gain / Split Count)')
        plt.title('Top 15 Most Important Features')
        plt.tight_layout()
        plt.savefig(os.path.join(reports_dir, "feature_importance.png"), dpi=150)
        plt.close()
    except Exception as e:
        print(f"Feature importance plot skipped: {e}")

if __name__ == "__main__":
    report = evaluate_models()
    print(json.dumps(report, indent=2))
