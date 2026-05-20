# Diabetes Risk Pipeline

A multi-stage distributed ML pipeline for early diabetes detection, built with PySpark on Google Cloud Dataproc. Trained on 100,000 anonymized records, it produces calibrated risk scores and cohort-level aggregations to support clinical triage and resource allocation.

**AUC-ROC: 0.9672 (Random Forest) | 0.9588 (Logistic Regression)**

---

## Team Members

- Sneha Basnet
- Krish Makwana
- Justin Tan
- Prathana Dankhara

---

## Tech Stack

| Layer | Tools |
|---|---|
| Compute | Google Cloud Dataproc, PySpark 4.0.2 |
| Storage | Google Cloud Storage (GCS), Parquet |
| ML | PySpark MLlib - Logistic Regression (Platt calibration), Random Forest |
| Evaluation | AUC-ROC, AUC-PR, Brier score, confusion matrix, feature importance |
| Visualization | Jupyter Notebooks |

---

## Dataset

**Source:** [Kaggle - 100,000 Diabetes Clinical Dataset](https://www.kaggle.com/datasets/priyamchoksi/100000-diabetes-clinical-dataset/data)  
**Size:** 100,000 records, 16 features, 5.9 MB  
**Records:** Anonymized patient encounters from U.S. electronic health systems, 53 states and territories (2015–2022)  
**Target:** `diabetes` (0 = no, 1 = yes) - ~8.5% positive class (class imbalance handled via sample weighting)

> The raw CSV is not committed to this repository. Download it from Kaggle and place it at `data/raw_data/diabetes_dataset.csv` before running any pipeline steps.

---

## Pipeline

Six sequential PySpark jobs run on GCP Dataproc:

### 01 - Preprocessing
Loads the raw CSV from GCS, drops nulls on required columns, applies clinical range filters (e.g. HbA1c 3.5–15.0, glucose 20–600, BMI 10–80), and writes a clean Parquet table. Assigns a stable `row_id` for downstream joins.

### 02 - Feature Engineering
Performs a **stratified 70/10/20 split** (train / calibration / test) per class to preserve the ~8.5% diabetic ratio across all sets. Assembles a `VectorAssembler` feature vector from six clinical inputs and writes three split tables to GCS.

**Features:** `hbA1c_level`, `blood_glucose_level`, `bmi`, `age`, `hypertension`, `heart_disease`

### 03 - Logistic Regression (3 jobs)
- **03\_01** - Trains a class-weighted LR with `StandardScaler` (fit on train only to prevent data leakage). Targets pre-lab screening via calibrated probability output.
- **03\_02** - Fits a **Platt calibration** model on the held-out calibration split so raw LR scores become reliable risk probabilities.
- **03\_03 + 03\_04** - Applies calibration to the test set, assigns risk bands (Low / Moderate / High), and writes stratified predictions to GCS.

### 04 - Random Forest (3 jobs)
- **04\_01** - Trains a class-weighted RF (20 trees, max depth 3, subsampling 0.7) for full binary classification and feature interpretability.
- **04\_02** - Evaluates on the test set: AUC-ROC, AUC-PR, Brier score, and confusion matrix.
- **04\_03** - Extracts and saves feature importance scores, identifying `blood_glucose_level` (0.418) and `hbA1c_level` (0.416) as the dominant predictors, together accounting for ~83% of model decisions.

### 05 - Final Artifact
Joins LR calibrated probabilities, RF predictions, and raw feature values into a single patient-level table. Validates all evaluation outputs and writes a `manifest.json` to GCS confirming artifact completeness.

### 06 - Risk Aggregation
Aggregates calibrated risk across six clinical dimensions (HbA1c bands, glucose bands, BMI bands, age groups, hypertension, heart disease) and writes cohort-level summaries for downstream dashboards.

---

## Results

| Model | AUC-ROC | AUC-PR | Brier | Accuracy | F1 | Recall |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.9588 | 0.8105 | 0.0357 | 93.8% | 0.668 | **0.774** |
| Random Forest | 0.9672 | 0.8342 | 0.0754 | - | - | - |

Recall was a primary design objective. In a clinical screening context, a missed diabetic patient (false negative) carries a higher cost than a false alarm. For the LR model, the classification threshold was lowered from the default 0.5 to 0.31 to increase sensitivity, accepting lower precision in exchange for catching more at-risk patients.

---

## Repository Structure

```
.
├── README.md
├── gcp.md                           - GCP Dataproc setup and job submission
├── data/
│   └── raw_data/                    - place diabetes_dataset.csv here (not tracked)
├── scripts/                         - past sprint shell scripts and utilities
├── docs/                            - supplementary documentation
└── diabetes_pipeline/
    ├── code/                        - 01_preprocessing through 06_risk_aggregation
    ├── evaluation/                  - model metrics and feature importance (from GCS)
    ├── aggregations/                - risk aggregation outputs (from GCS)
    └── visualization/               - dataset_overview.ipynb, model_results.ipynb
```

---

## Running the Pipeline

1. Place the raw dataset at `data/raw_data/diabetes_dataset.csv`
2. See [gcp.md](gcp.md) for GCP cluster setup and job submission steps
3. View results in `diabetes_pipeline/visualization/` notebooks
