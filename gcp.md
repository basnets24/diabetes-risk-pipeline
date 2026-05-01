# GCP Dataproc Commands

## Project Info

| Field | Value |
|-------|-------|
| Project ID | `team10-diabetes-final-sprint` |
| Project Number | `124820512231` |
| Region | `us-west1` |
| Cluster Name | `diabetes-cluster-ml` |

## Prerequisites

```bash
# Set your project and region once
gcloud config set project team10-diabetes-final-sprint
gcloud config set dataproc/region us-west1
```

---

## 1. Start the Dataproc Cluster

```bash
gcloud dataproc clusters start diabetes-cluster-ml \
  --region=us-west1
```

---

## 2. Upload Scripts to GCS

Run this before submitting any jobs:

```bash
gsutil cp diabetes_pipeline/code/*.py gs://team10-diabetes-data/code/
```

---

## 3. Submit Individual PySpark Jobs

Run these in order — each job depends on the output of the previous.

### 1. Feature Engineering
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/feature_engineering.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 2. Logistic Regression — Model
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/logistic_regression_model.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 3. Logistic Regression — Evaluation
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/logistic_regression_eval.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 4. Random Forest — Model
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/random_forest_model.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 5. Random Forest — Evaluation & Feature Importance
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/random_forest_eval.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 6. Risk Aggregation
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/risk_aggregation.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 7. Final Artifact
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/final_artifact.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

**Key flags:**
| Flag | Description |
|------|-------------|
| `--cluster` | Name of the cluster to run the job on |
| `--region` | Must match the cluster's region |
| `--properties` | Optional: Spark config overrides (e.g. `spark.executor.memory=4g`) |

---

## 4. Run the Full Pipeline via Workflow Template

### Create the workflow template (one-time setup)
```bash
gcloud dataproc workflow-templates create diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates set-cluster-selector diabetes-pipeline \
  --region=us-west1 \
  --cluster-labels=goog-dataproc-cluster-name=diabetes-cluster-ml

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/feature_engineering.py \
  --step-id=feature-engineering \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/logistic_regression_model.py \
  --step-id=lr-model \
  --start-after=feature-engineering \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/logistic_regression_eval.py \
  --step-id=lr-eval \
  --start-after=lr-model \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/random_forest_model.py \
  --step-id=rf-model \
  --start-after=lr-eval \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/random_forest_eval.py \
  --step-id=rf-eval \
  --start-after=rf-model \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/risk_aggregation.py \
  --step-id=risk-aggregation \
  --start-after=rf-eval \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://team10-diabetes-data/code/final_artifact.py \
  --step-id=final-artifact \
  --start-after=risk-aggregation \
  --workflow-template=diabetes-pipeline \
  --region=us-west1
```

### Run the pipeline
```bash
gcloud dataproc workflow-templates instantiate diabetes-pipeline \
  --region=us-west1
```

### Check pipeline status
```bash
gcloud dataproc operations list --region=us-west1
```

> **Note:** To re-run after code changes, re-upload scripts with `gsutil cp` and instantiate again — the template stays saved.

---

## 5. Download Outputs

```bash
gsutil cp gs://team10-diabetes-data/evaluation/confusion_matrix_lr.csv .
gsutil cp gs://team10-diabetes-data/evaluation/confusion_matrix_rf.csv .
gsutil cp gs://team10-diabetes-data/manifest.json .
gsutil -m cp -r gs://team10-diabetes-data/aggregations/ .
```

---

## 6. Stop the Dataproc Cluster

Stop the cluster when done to avoid charges.

```bash
gcloud dataproc clusters stop diabetes-cluster-ml \
  --region=us-west1
```

---

## Quick Reference

```bash
# List all clusters
gcloud dataproc clusters list --region=us-west1

# Check cluster status
gcloud dataproc clusters describe diabetes-cluster-ml --region=us-west1

# List submitted jobs
gcloud dataproc jobs list --cluster=diabetes-cluster-ml --region=us-west1

# Check a specific job's status
gcloud dataproc jobs describe JOB_ID --region=us-west1
```
