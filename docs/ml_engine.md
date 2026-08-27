# ChargeShield ML Win-Probability Engine Specification & Report

> **Project:** ChargeShield — AI-Powered Chargeback Defense & Recovery Platform  
> **Track:** Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager  
> **Status:** Phase 2 ML Win-Probability Engine Completed  

---

## 1. Executive Summary & Problem Formulation

The **ChargeShield ML Win-Probability Engine** estimates the probability that a merchant will successfully contest a filed chargeback dispute:

$$P(\text{contest\_success} = 1 \mid \mathcal{X}_{\text{triage}})$$

Unlike generic payment fraud detection models (which attempt to block bad checkout attempts), this model operates at **dispute triage time**. It provides cost-sensitive decision support answering:

> *"Based on evidence available at the time the chargeback is received, should the merchant spend time and money contesting this dispute?"*

---

## 2. Model Evaluation Summary (Held-Out Test Set: $N=96$)

Evaluation conducted on a strict chronological 20% held-out test set ($N=96$ disputes, 85.4% true win rate):

| Metric | Baseline (Logistic Regression) | Primary (LightGBM — Default $t=0.50$) | **Primary (LightGBM — Optimal $t=0.29$)** |
|---|---|---|---|
| **Accuracy** | 89.58% | 88.54% | **90.62%** |
| **Precision (Win)** | 91.86% | 92.77% | **91.01%** |
| **Recall (Win)** | 96.34% | 93.90% | **98.78%** |
| **F1-Score** | 0.9405 | 0.9333 | **0.9474** |
| **ROC-AUC** | 0.9303 | 0.8850 | **0.8850** |
| **PR-AUC** | **0.9866** | 0.9746 | **0.9746** |
| **Brier Score** | 0.0693 | 0.0822 | **0.0822** |
| **Total Test Cost (₹)** | ₹11,344.38 (Naive) | ₹10,302.72 | **₹6,661.73** |
| **Cost Savings** | ₹0 (Baseline) | ₹1,041.66 (9.2%) | **₹4,682.65 (41.3% reduction)** |

---

## 3. Cost-Sensitive Decision Threshold Optimization

Rather than using a fixed 0.50 cutoff, ChargeShield optimizes a decision threshold $t^*$ on the **Validation Set** ($N=95$) to minimize total expected financial cost:

$$\text{Expected Cost}(t) = C_{\text{FP}} \sum_{i \in FP(t)} \text{Amount}_i + C_{\text{FN}} \sum_{j \in FN(t)} \text{Amount}_j$$

where:
- $C_{\text{FP}} = 0.25$: Merchant fee and operational friction of contesting a dispute that is ultimately lost.
- $C_{\text{FN}} = 1.00$: 100% loss of recoverable revenue when failing to contest a winnable dispute.

### Operational Policy Formulation
- **CONTEST:** $P(\text{win}) \ge 0.29$
- **MANUAL REVIEW:** $0.15 \le P(\text{win}) < 0.29$
- **DO NOT CONTEST:** $P(\text{win}) < 0.15$

---

## 4. SHAP Feature Explainability

Every prediction includes real-time SHAP (SHapley Additive exPlanations) attributions from the trained LightGBM TreeExplainer:

- **Top Positive Factors:** Proof of Delivery (POD) signature presence, customer tenure, device fingerprint match, prior support resolution.
- **Top Negative Factors:** Authorization risk score $>80$, missing delivery confirmation, prior lost chargebacks ($>1$).

---

## 5. Artifact Registry & Model Commands

### Model Artifacts (`ml/artifacts/`)
- `model.joblib`: Dict containing LightGBM model, Logistic Regression baseline, fitted preprocessor, and optimal threshold.
- `preprocessor.joblib`: Scikit-learn ColumnTransformer fitted exclusively on training set.
- `metadata.json`: Model version `chargeshield_ml_v1`, random seed `42`, dataset statistics.

### Reports & Visualizations (`ml/reports/`)
- `roc_curve.png`, `pr_curve.png`, `calibration_curve.png`, `confusion_matrix.png`, `feature_importance.png`, `shap_summary.png`.

### Commands
```powershell
# Train models & optimize cost threshold
python -m ml.train

# Evaluate models on held-out test set
python -m ml.evaluate

# Test structured prediction API
python -m ml.predict

# Run full test suite
python -m pytest tests/
```

---

## 6. Limitations & Disclaimer

> [!NOTE]
> All model evaluation metrics, PR-AUC figures, and SHAP feature attributions are derived from synthetic relational merchant datasets (`data/generator.py`, seed 42). The system is designed for hackathon/technical demonstration and does not interact with live card networks or Razorpay production databases.
