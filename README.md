# Team 10 - Comprehensive Diabetes Clinical Dataset Analysis

## Team Members
- Justin Tan
- Sneha Basnet
- Prathana Dankhara
- Krish Makwana

---

## Dataset

**Title:** 100,000 Diabetes Clinical Dataset  
**Source:** [Kaggle — Priyam Choksi](https://www.kaggle.com/datasets/priyamchoksi/100000-diabetes-clinical-dataset/data)  
**Size:** 100,000 records, 16 features  
**Format:** CSV (5.9 MB uncompressed)

Each record is an anonymized patient encounter aggregated from U.S. electronic health systems across 53 states and territories (2015–2022). The target variable is `diabetes` (0 = no, 1 = yes); prevalence is ~8.5%.

> The raw CSV is not committed to this repository. Download it from Kaggle and place it at `data/raw_data/diabetes_dataset.csv` before running any pipeline steps.

---

## Repository Structure

```
.
├── README.md                        — this file
├── gcp.md                           — GCP Dataproc setup and job submission
├── data/
│   └── raw_data/                    — place diabetes_dataset.csv here (not tracked)
├── scripts/                         — past sprint shell scripts and utilities
├── out/                             — evidence generated from scripts
├── docs/                            — supplementary documentation
└── diabetes_pipeline/               — ML pipeline (PySpark on GCP Dataproc)
    ├── code/                        — 01_preprocessing through 06_risk_aggregation
    ├── evaluation/                  — model metrics (downloaded from GCS)
    ├── aggregations/                — risk aggregation outputs (downloaded from GCS)
    └── visualization/               — dataset_overview.ipynb, model_results.ipynb
```

---

## ML Pipeline Overview

The ML pipeline runs on **GCP Dataproc** (PySpark 4.0.2). Two models are trained and evaluated on a 70/10/20 stratified split:

- **Logistic Regression:** Pre-lab screening with calibrated risk scores (AUC-ROC: 0.9588)
- **Random Forest:** Full classification + feature interpretability (AUC-ROC: 0.9672)

**Feature set:** `hbA1c_level`, `blood_glucose_level`, `bmi`, `age`, `hypertension`, `heart_disease`

See [docs/logisticregression.md](docs/logisticregression.md) and [docs/randomforest.md](docs/randomforest.md) for detailed pipeline documentation.

## What the pipeline does

- Cleans and filters the raw clinical CSV into a compact, analysis-ready table.
- Builds stratified train / calibration / test feature sets and assembles model-ready vectors.
- Trains logistic regression (with Platt calibration) and random forest models on GCP Dataproc.
- Produces calibrated per-record risk probabilities, risk-band assignments, and evaluation metrics written to GCS.

## Why this is useful (for stakeholders and users)

- Clinicians: receives calibrated patient-risk scores to support early detection and prioritize high-risk patients for follow-up.
- Health system managers: uses aggregated risk and cohort-level trends to allocate screening resources and plan interventions.
- Data teams & implementers: gains reproducible artifacts (models, predictions, metrics) and GCS outputs for deployment, monitoring, and auditing.
- Researchers & quality teams: enables reproducible comparisons between models, supporting evaluation of interventions and policy decisions.
- Patients and care coordinators: supports targeted outreach and personalized screening to improve outcomes and reduce missed diagnoses.

---

## Running the Pipeline

1. Ensure GCP access to project `team10-diabetes-final-sprint` and raw dataset at `data/raw_data/diabetes_dataset.csv`
2. See [gcp.md](gcp.md) for step-by-step cluster setup and job submission
3. View results in `diabetes_pipeline/visualization/` notebooks
