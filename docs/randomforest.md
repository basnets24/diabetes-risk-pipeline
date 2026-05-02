Random Forest — Diabetes Classification and Feature Analysis
=============================================================

Overview
--------
We use a Random Forest classifier to predict diabetes from six clinical
features. Unlike Logistic Regression, Random Forest does not require feature
scaling and natively produces feature importance scores — making it useful
both as a classifier and as an interpretability tool for understanding which
features drive diabetes risk most.

The pipeline runs across three Spark jobs on Google Dataproc.

Key difference from the LR pipeline: no Platt calibration step. RF
probabilities are generally closer to true prevalence than class-weighted LR,
so we evaluate them directly. The Brier score in step 2 confirms whether
calibration is needed.


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

All features are numeric; no encoding or scaling is needed for RF.

Split: stratified 70 / 10 / 20 (train / calibration / test), preserving the
~8.5% diabetic ratio across all three sets. RF uses only the train and test
splits — the calibration split is not used.


Pipeline Steps
--------------

1. Model Training (04_01_rf_model.py)
   - Loads the pre-split stratified train set from GCS (Parquet).
   - Computes class weights from the training label distribution to handle
     class imbalance (~8.5% diabetic). Same weighting scheme as LR:
       weight_for_1 = neg / total
       weight_for_0 = pos / total
   - Trains RandomForestClassifier with:
       numTrees=20, maxDepth=3, maxBins=16, subsamplingRate=0.7, seed=42
     Conservative settings chosen to avoid OOM on Dataproc. maxDepth=3
     keeps each tree shallow; subsamplingRate=0.7 adds row-level bagging.
   - Saves the trained model to GCS.

2. Evaluation (04_02_rf_eval.py)
   - Loads the saved RF model from GCS.
   - Transforms the test feature table through the RF model in Spark, then
     extracts the class-1 probability as prob_diabetic via vector_to_array.
     Feature vectors are dropped immediately after extraction to keep memory
     usage low.
   - Collects (row_id, diabetes, prob_diabetic) to pandas — small collect,
     only three columns.
   - Computes all metrics with sklearn (no Spark ML evaluators):

   Discrimination metrics (all threshold-free):
   - AUC-ROC: 0.9672 — overall discrimination ability across all thresholds.
   - AUC-PR:  0.8342 — precision-recall AUC, more informative under class
     imbalance (8.5% positive class).
   - Brier:   0.0754 — mean squared error between predicted probability and
     true label. A low Brier score indicates RF probabilities are reasonably
     calibrated without Platt scaling.

   No threshold-based metrics (confusion matrix, sensitivity, specificity) are
   computed for RF. Only AUC-ROC, AUC-PR, and Brier are stored.

   Saves:
   - predictions/rf_scored_test    scored test set (row_id, diabetes, prob_diabetic)
   - evaluation/metrics_rf/        AUC-ROC, AUC-PR, Brier in a single CSV

3. Feature Importance (04_03_rf_features.py)
   - Loads the saved RF model from GCS (no data scan needed — importances
     are stored in the model object itself).
   - Extracts Gini-based feature importances via featureImportances.toArray():
     each score reflects how much that feature reduces impurity across all
     trees, averaged and normalised to sum to 1.
   - Ranks features from most to least important.

   Actual results:
     1. blood_glucose_level   0.4180  (41.8%)
     2. hbA1c_level           0.4160  (41.6%)
     3. age                   0.1330  (13.3%)
     4. bmi                   0.0270  ( 2.7%)
     5. hypertension          0.0060  ( 0.6%)
     6. heart_disease         0.0000  ( 0.0%)

   This answers: "Which features are most predictive of diabetes?"
   Blood glucose and HbA1c together account for ~83% of total importance,
   consistent with clinical reality — these are the primary diagnostic
   markers. Heart disease contributes 0% once lab values are included.

   Saves:
   - evaluation/feature_importance_rf/   ranked features with importance scores (CSV)


How the Output Is Used
----------------------
  prob_diabetic       — RF's estimated probability of diabetes for each
                        test record. Used to compare model discrimination
                        against the LR calibrated probability (AUC comparison).

  feature importance  — The ranked list directly answers which features
                        matter most for prediction. High importance for
                        blood_glucose_level and hbA1c_level validates that
                        the model is learning clinically meaningful patterns.
                        Near-zero importance for hypertension and heart_disease
                        confirms those features add no discriminative power
                        beyond the lab values, despite their strong univariate
                        association with diabetes.

Comparison with LR:
  - RF AUC-ROC (0.9672) slightly exceeds LR AUC-ROC (0.9588): RF captures
    non-linear interactions (e.g. glucose × age) that LR cannot model.
  - RF AUC-PR (0.8342) exceeds LR AUC-PR (0.8094): RF is more precise at
    the top of the risk ranking under class imbalance.
  - LR provides calibrated probabilities (via Platt) and a full confusion
    matrix with tuned threshold. RF provides only AUC and Brier — no
    threshold-based metrics are stored in the current pipeline.
  - RF Brier score (0.0754) is low, suggesting calibration is not required.


GCS Outputs
-----------
| Path                              | Description |
|---|---|
| `models/rf_model` | Trained Random Forest model |
| `predictions/rf_scored_test` | Test set with row_id, diabetes, prob_diabetic |
| `evaluation/metrics_rf/` | AUC-ROC, AUC-PR, Brier (CSV) |
| `evaluation/feature_importance_rf/` | Ranked feature importances (CSV) |
