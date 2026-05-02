Logistic Regression — Diabetes Risk Classification
====================================================

Overview
--------
We use a Logistic Regression model to estimate the probability of diabetes for
each record. The output is a calibrated probability (0–1) that reflects true
population prevalence, which we then use to assign each record to a
Low / Medium / High risk band.

The pipeline runs across four Spark jobs on Google Dataproc, writing
intermediate results to GCS at each step.

Key difference from the RF pipeline: LR requires StandardScaler (gradient
descent is sensitive to feature scale) and Platt calibration (class weighting
inflates raw probabilities by ~2.6× relative to true prevalence).


Features
--------
The same six-feature vector built by 02_feature_engineering.py is used for
both models:
  - hbA1c_level          HbA1c (glycated haemoglobin), primary diabetes marker
  - blood_glucose_level  Fasting or random blood glucose reading
  - bmi                  Body mass index
  - age                  Age in years
  - hypertension         Binary: 1 if diagnosed with hypertension
  - heart_disease        Binary: 1 if diagnosed with heart disease

Split: stratified 70 / 10 / 20 (train / calibration / test), preserving the
~8.5% diabetic ratio across all three sets.


Pipeline Steps
--------------

1. Model Training (03_01_lr_model.py)
   - Loads the pre-split stratified train set from GCS (Parquet).
   - Computes class weights from the training label distribution to handle
     class imbalance (~8.5% diabetic):
       weight_for_1 = neg / total
       weight_for_0 = pos / total
   - Fits a StandardScaler (withMean=True, withStd=True) on the training set
     only. Scaling is necessary because LR uses gradient descent — unscaled
     features (e.g. blood_glucose 80–400 vs binary 0/1) cause uneven
     convergence.
   - Trains LogisticRegression with class-weighted samples:
       maxIter=20, tol=1e-6
   - Logs convergence iteration to confirm the solver did not hit maxIter
     prematurely.
   - Saves the trained LR model and fitted scaler to GCS.

2. Platt Calibration — Fit (03_02_lr_calibration.py)
   - Loads the LR model and scaler from GCS.
   - Scores the calibration set: applies scaler → LR, then immediately
     projects down to (diabetes, prob_diabetic_raw) to avoid OOM on large
     feature vectors.
   - Checkpoints the scored calibration set to GCS to break the Spark
     lineage chain and free executor memory before fitting.
   - Fits a second LogisticRegression (Platt model) on (prob_diabetic_raw,
     diabetes):
       maxIter=25, tol=1e-4
   - The Platt model learns to map raw LR scores to calibrated probabilities
     that match true prevalence. Pre-calibration average was ~0.215; true
     prevalence is ~0.082 — a 2.6× overestimate corrected by Platt scaling.
   - Saves the fitted Platt model to GCS.

3. Platt Calibration — Apply (03_03_lr_apply_calibration.py)
   - Loads the LR model, scaler, and Platt model from GCS.
   - Applies the full pipeline (scale → LR score → Platt scale) to both the
     calibration and test sets. Feature vectors are dropped immediately after
     the LR transform to keep memory usage low.
   - Outputs per record: prob_diabetic_raw, prob_diabetic, platt_prediction,
     diabetes (and row_id for the test set).
   - Prints a calibration check for each split:
       pre-cal avg  ~0.2150  (raw LR, inflated by class weighting)
       post-cal avg ~0.0820  (after Platt)
       true prev    ~0.0820  (ground truth)
     post-cal avg ≈ true prevalence confirms calibration succeeded.
   - Saves calibrated predictions to GCS.

4. Evaluation and Risk Stratification (03_04_risk.py)
   - Collects calibrated cal and test predictions into pandas (only
     prob_diabetic and diabetes columns — small collect).

   AUC metrics (sklearn, computed on test set):
   - AUC-ROC: 0.9588
   - AUC-PR:  0.8094
   These are rank-based and unchanged by calibration, but computed here to
   keep all final metrics in one place.

   Brier score:
   - Mean squared error between predicted probability and true label.
   - A low Brier score alongside post-cal avg ≈ true prevalence confirms
     the calibrated probabilities are reliable.

   Threshold tuning (F2-max on calibration set):
   - Sweeps the precision-recall curve on calibration set probabilities.
   - Selects the threshold that maximises F2 (β=2), which weights recall
     twice as heavily as precision — appropriate because missing a diabetic
     case is more costly than a false positive.
   - Tuned threshold: 0.3062
   - Applies threshold to test set to compute confusion matrix.

   Confusion matrix results (test set):
   - Sensitivity: 0.7735   Specificity: 0.9521
   - Precision:   ~0.59    F1: 0.67    Accuracy: 0.9376
   - TP=1260  TN=17576  FP=~870  FN=~370

   Risk stratification:
   - Derives band thresholds from calibration set percentiles:
       Medium threshold (p80): 0.0456
       High threshold   (p90): 0.3562
   - Assigns each test record to Low / Medium / High in Spark:
       Low:    prob_diabetic <  0.0456  (bottom 80%)
       Medium: prob_diabetic >= 0.0456  and < 0.3562  (80th–90th percentile)
       High:   prob_diabetic >= 0.3562  (top 10%)
   - Risk band summary (test set):
       Low     n=16058  avg_prob=0.005  diabetic_rate=0.011
       Medium  n= 2056  avg_prob=0.152  diabetic_rate=0.112
       High    n= 1976  avg_prob=0.628  diabetic_rate=0.620

   All metrics (AUC, Brier, threshold, confusion matrix values) are saved to
   GCS as a single CSV. Risk band thresholds are printed to the Dataproc logs
   but not persisted to a file.


How the Output Is Used
----------------------
The final deliverable for each record is:

  prob_diabetic   — calibrated probability of diabetes (0–1).
                    Interpretable: 0.20 means an estimated 20% chance.

  risk_band       — Low / Medium / High, derived from population
                    percentiles on the calibration set:
                    Low:    bottom 80% by predicted risk  (< 0.046)
                    Medium: 80th–90th percentile          (0.046 – 0.356)
                    High:   top 10% by predicted risk     (>= 0.356)

The calibration table validates that prob_diabetic is reliable: a record
assigned 0.30 has approximately a 30% estimated probability of being diabetic.
This is what makes the score actionable rather than just a ranking.


GCS Outputs
-----------
| Path                            | Description |
|---|---|
| `models/lr_model` | Trained LR model |
| `models/lr_scaler` | Fitted StandardScaler |
| `models/platt_model` | Fitted Platt calibration model |
| `predictions/lr_calibrated_cal` | Calibrated calibration-set predictions |
| `predictions/lr_calibrated_test` | Calibrated test-set predictions |
| `predictions/lr_risk_stratified` | Test set with risk_band column |
| `evaluation/metrics_lr/` | AUC-ROC, AUC-PR, Brier, threshold, confusion matrix (CSV) |
| `evaluation/risk_summary_lr/` | Per-band n, avg_prob, diabetic_rate (CSV) |
