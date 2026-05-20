# GCP Dataproc Commands

## Project Info

| Field | Value |
|-------|-------|
| Project ID | `YOUR_GCP_PROJECT_ID` |
| Project Number | `YOUR_PROJECT_NUMBER` |
| Region | `us-west1` |
| Cluster Name | `diabetes-cluster-ml` |

## Prerequisites

```bash
# Set your project and region once
gcloud config set project YOUR_GCP_PROJECT_ID
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
gsutil cp diabetes_pipeline/code/*.py gs://YOUR_GCS_BUCKET/code/
```

---

## 3. Submit Individual PySpark Jobs

Run these in order — each job depends on the output of the previous.

### 1. Preprocessing
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/01_preprocessing.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 2. Feature Engineering
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/02_feature_engineering.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 3. LR — Train Model
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/03_01_lr_model.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 4. LR — Fit Platt Calibration
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/03_02_lr_calibration.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 5. LR — Apply Calibration
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/03_03_lr_apply_calibration.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 6. LR — Evaluation & Risk Stratification
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/03_04_risk.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 7. RF — Train Model
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/04_01_rf_model.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 8. RF — Evaluation
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/04_02_rf_eval.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 9. RF — Feature Importance
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/04_03_rf_features.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 10. Final Artifact
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/05_final_artifact.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### 11. Risk Aggregation
```bash
gcloud dataproc jobs submit pyspark \
  gs://YOUR_GCS_BUCKET/code/06_risk_aggregation.py \
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



### Delete old template (if it exists)
```bash
gcloud dataproc workflow-templates delete diabetes-pipeline \
  --region=us-west1
```

### Create the workflow template (one-time setup)
```bash
gcloud dataproc workflow-templates create diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates set-cluster-selector diabetes-pipeline \
  --region=us-west1 \
  --cluster-labels=goog-dataproc-cluster-name=diabetes-cluster-ml

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/01_preprocessing.py \
  --step-id=preprocessing \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/02_feature_engineering.py \
  --step-id=feature-engineering \
  --start-after=preprocessing \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/03_01_lr_model.py \
  --step-id=lr-model \
  --start-after=feature-engineering \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/03_02_lr_calibration.py \
  --step-id=lr-calibration \
  --start-after=lr-model \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/03_03_lr_apply_calibration.py \
  --step-id=lr-apply \
  --start-after=lr-calibration \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/03_04_risk.py \
  --step-id=lr-risk \
  --start-after=lr-apply \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/04_01_rf_model.py \
  --step-id=rf-model \
  --start-after=feature-engineering \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/04_02_rf_eval.py \
  --step-id=rf-eval \
  --start-after=rf-model \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/04_03_rf_features.py \
  --step-id=rf-features \
  --start-after=rf-eval \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/05_final_artifact.py \
  --step-id=final-artifact \
  --start-after=lr-risk,rf-features \
  --workflow-template=diabetes-pipeline \
  --region=us-west1

gcloud dataproc workflow-templates add-job pyspark \
  gs://YOUR_GCS_BUCKET/code/06_risk_aggregation.py \
  --step-id=risk-aggregation \
  --start-after=final-artifact \
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
# Metrics
gsutil -m cp -r gs://YOUR_GCS_BUCKET/evaluation/ .

# Final patient-level dataset
gsutil -m cp -r gs://YOUR_GCS_BUCKET/predictions/v2_final_dataset/ .

# Manifest
gsutil cp gs://YOUR_GCS_BUCKET/manifest.json .
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
