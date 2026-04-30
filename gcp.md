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

## 2. Submit a PySpark Job

### Feature Engineering
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/feature_engineering.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

### Logistic Regression Model
```bash
gcloud dataproc jobs submit pyspark \
  gs://team10-diabetes-data/code/logistic_regression_model.py \
  --cluster=diabetes-cluster-ml \
  --region=us-west1
```

> **Note:** Upload your scripts to GCS before submitting:


**Key flags:**
| Flag | Description |
|------|-------------|
| `--cluster` | Name of the cluster to run the job on |
| `--region` | Must match the cluster's region |
| `--jars` | Optional: extra JARs to add to the classpath |
| `--properties` | Optional: Spark config overrides (e.g. `spark.executor.memory=4g`) |

---

## 3. Stop the Dataproc Cluster

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
